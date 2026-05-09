import json
import logging
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from odoo import api, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class RegionSyncService(models.AbstractModel):
    _name = 'id.region.sync.service'
    _description = 'Indonesia Region Sync Service'

    @api.model
    def _base_urls(self):
        configured = self.env['ir.config_parameter'].sudo().get_param(
            'id_region.api_base_url',
            'https://wilayah.id/api',
        ).rstrip('/')
        fallbacks = [
            'https://www.emsifa.com/api-wilayah-indonesia/api',
            'https://raw.githubusercontent.com/emsifa/api-wilayah-indonesia/master/api',
        ]
        urls = [configured]
        for url in fallbacks:
            if url not in urls:
                urls.append(url)
        return urls

    @api.model
    def _extract_rows(self, payload):
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict) and isinstance(payload.get('data'), list):
            return payload['data']
        return []

    @api.model
    def _row_code(self, row):
        return str(row.get('id') or row.get('code') or '').strip()

    @api.model
    def _row_name(self, row):
        return str(row.get('name') or row.get('value') or '').strip()

    @api.model
    def _row_zip(self, row):
        return (row.get('postal_code') or row.get('zip') or '').strip() or False

    @api.model
    def _norm_text(self, text):
        return ' '.join((text or '').strip().lower().split())

    @api.model
    def _resolve_scope_state(self, province_code):
        """Resolve selected province to canonical API-backed state record."""
        state = self.env['res.country.state'].sudo().search([('code', '=', province_code)], limit=1)
        if not state:
            return False

        api_rows = self._fetch_rows('provinces.json')
        api_by_code = {self._row_code(r): r for r in api_rows if self._row_code(r)}
        if province_code in api_by_code:
            return state

        # User may select a non-API code state; map by province name.
        state_name_key = self._norm_text(state.name)
        mapped_row = next((r for r in api_rows if self._norm_text(self._row_name(r)) == state_name_key), None)
        if not mapped_row:
            return state

        api_code = self._row_code(mapped_row)
        if not api_code:
            return state

        country = self._get_id_country()
        canonical_state = self.env['res.country.state'].sudo().search([
            ('country_id', '=', country.id),
            ('code', '=', api_code),
        ], limit=1)
        if canonical_state:
            return canonical_state

        # Ensure canonical state exists so scoped city/district relations can be found.
        return self.env['res.country.state'].sudo().create({
            'name': self._row_name(mapped_row),
            'code': api_code,
            'country_id': country.id,
        })

    @api.model
    def _fetch_rows(self, path):
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (X11; Linux x86_64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/124.0.0.0 Safari/537.36'
            ),
            'Accept': 'application/json,text/plain,*/*',
        }

        errors = []
        for base_url in self._base_urls():
            url = f"{base_url}/{path.lstrip('/')}"
            try:
                request = Request(url, headers=headers)
                with urlopen(request, timeout=45) as response:
                    payload = response.read().decode('utf-8')
                rows = self._extract_rows(json.loads(payload))
                if rows:
                    _logger.info('Region sync fetch ok: %s (rows=%s)', url, len(rows))
                    return rows
                errors.append(f'{url} (empty or unsupported response format)')
            except (URLError, HTTPError, json.JSONDecodeError) as err:
                errors.append(f'{url} ({err})')

        raise UserError('Failed to fetch Indonesia region API from all sources: ' + '; '.join(errors))

    @api.model
    def _get_id_country(self):
        country = self.env.ref('base.id', raise_if_not_found=False)
        if country:
            return country
        country = self.env['res.country'].sudo().search([('code', '=', 'ID')], limit=1)
        if country:
            return country
        return self.env['res.country'].sudo().create({'name': 'Indonesia', 'code': 'ID'})

    @api.model
    def _notify(self, title, message):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': message,
                'type': 'success',
                'sticky': True,
            },
        }

    @api.model
    def _prefetch_map(self, model, domain=None):
        domain = domain or []
        return {
            row['code']: row['id']
            for row in self.env[model].sudo().search_read(domain, ['code'])
            if row.get('code')
        }

    @api.model
    def _upsert_by_code(self, model, code, vals, cache):
        if code in cache:
            self.env[model].sudo().browse(cache[code]).write(vals)
            return False
        vals['code'] = code
        rec = self.env[model].sudo().create(vals)
        cache[code] = rec.id
        return True

    @api.model
    def _deactivate_missing(self, model, seen_codes, domain=None):
        domain = list(domain or [])
        if seen_codes:
            domain.append(('code', 'not in', list(seen_codes)))
        else:
            domain.append(('code', '=', '__no_code__'))
        self.env[model].sudo().search(domain).write({'active': False})

    @api.model
    def action_sync_provinces(self):
        _logger.info('Region sync started: provinces')
        country = self._get_id_country()
        state_model = self.env['res.country.state'].sudo()
        state_by_code = self._prefetch_map('res.country.state', [('country_id', '=', country.id)])

        created = updated = 0
        seen_codes = set()

        for province in self._fetch_rows('provinces.json'):
            code = self._row_code(province)
            if not code:
                continue
            seen_codes.add(code)
            vals = {
                'name': self._row_name(province),
                'code': code,
                'country_id': country.id,
            }
            if self._upsert_by_code('res.country.state', code, vals, state_by_code):
                created += 1
            else:
                updated += 1

        self.env['res.country.state'].sudo().search([
            ('country_id', '=', country.id),
            ('code', 'not in', list(seen_codes) or ['__no_code__']),
        ]).unlink()

        _logger.info('Region sync finished: provinces(c=%s,u=%s)', created, updated)
        return self._notify('Indonesia Region Sync', 'Province sync completed successfully.')

    @api.model
    def action_sync_cities(self):
        _logger.info('Region sync started: cities')
        country = self._get_id_country()
        state_by_code = self._prefetch_map('res.country.state', [('country_id', '=', country.id)])
        city_by_code = self._prefetch_map('res.city', [])

        created = updated = 0
        seen_codes = set()

        for province in self._fetch_rows('provinces.json'):
            province_code = self._row_code(province)
            if not province_code:
                continue
            state_id = state_by_code.get(province_code)
            if not state_id:
                continue
            for regency in self._fetch_rows(f'regencies/{province_code}.json'):
                code = self._row_code(regency)
                if not code:
                    continue
                seen_codes.add(code)
                vals = {
                    'name': self._row_name(regency),
                    'state_id': state_id,
                    'active': True,
                }
                if self._upsert_by_code('res.city', code, vals, city_by_code):
                    created += 1
                else:
                    updated += 1

        self._deactivate_missing('res.city', seen_codes)

        _logger.info('Region sync finished: cities(c=%s,u=%s)', created, updated)
        return self._notify('Indonesia Region Sync', 'City sync completed successfully.')

    @api.model
    def action_sync_districts(self, province_code=None):
        _logger.info('Region sync started: districts%s', province_code and f' (province={province_code})' or '')
        district_by_code = self._prefetch_map('res.district', [])

        created = updated = 0
        seen_codes = set()

        city_domain = []
        district_deactivate_domain = []
        if province_code:
            state = self._resolve_scope_state(province_code)
            if not state:
                raise UserError(f'Province code not found: {province_code}')
            city_domain = [('state_id', '=', state.id)]
            district_deactivate_domain = [('city_id.state_id', '=', state.id)]

        cities = self.env['res.city'].sudo().with_context(active_test=False).search(city_domain)
        if province_code and not cities:
            _logger.info(
                'Region sync districts scope has no cities for province=%s; running province+city sync first',
                province_code,
            )
            self.action_sync_provinces()
            self.action_sync_cities()
            state = self._resolve_scope_state(province_code)
            city_domain = [('state_id', '=', state.id)] if state else city_domain
            district_deactivate_domain = [('city_id.state_id', '=', state.id)] if state else district_deactivate_domain
            cities = self.env['res.city'].sudo().with_context(active_test=False).search(city_domain)
        _logger.info('Region sync districts scope: cities=%s', len(cities))
        for city in cities:
            for district in self._fetch_rows(f'districts/{city.code}.json'):
                code = self._row_code(district)
                if not code:
                    continue
                seen_codes.add(code)
                vals = {
                    'name': self._row_name(district),
                    'city_id': city.id,
                    'active': True,
                }
                if self._upsert_by_code('res.district', code, vals, district_by_code):
                    created += 1
                else:
                    updated += 1

        # Keep deactivation inside sync scope when province filter is used.
        self._deactivate_missing('res.district', seen_codes, district_deactivate_domain)

        _logger.info('Region sync finished: districts(c=%s,u=%s)', created, updated)
        return self._notify('Indonesia Region Sync', 'District sync completed successfully.')

    @api.model
    def action_sync_villages(self, province_code=None):
        _logger.info('Region sync started: villages%s', province_code and f' (province={province_code})' or '')
        village_by_code = self._prefetch_map('res.village', [])

        created = updated = 0
        seen_codes = set()

        district_domain = []
        village_deactivate_domain = []
        if province_code:
            state = self.env['res.country.state'].sudo().search([('code', '=', province_code)], limit=1)
            if not state:
                raise UserError(f'Province code not found: {province_code}')
            district_domain = [('city_id.state_id', '=', state.id)]
            village_deactivate_domain = [('district_id.city_id.state_id', '=', state.id)]

        districts = self.env['res.district'].sudo().with_context(active_test=False).search(district_domain)
        _logger.info('Region sync villages scope: districts=%s', len(districts))
        for district in districts:
            for village in self._fetch_rows(f'villages/{district.code}.json'):
                code = self._row_code(village)
                if not code:
                    continue
                seen_codes.add(code)
                vals = {
                    'name': self._row_name(village),
                    'district_id': district.id,
                    'zip': self._row_zip(village),
                    'active': True,
                }
                if self._upsert_by_code('res.village', code, vals, village_by_code):
                    created += 1
                else:
                    updated += 1

        # Keep deactivation inside sync scope when province filter is used.
        self._deactivate_missing('res.village', seen_codes, village_deactivate_domain)

        _logger.info('Region sync finished: villages(c=%s,u=%s)', created, updated)
        return self._notify('Indonesia Region Sync', 'Village sync completed successfully.')

    @api.model
    def action_sync_all_regions(self):
        self.action_sync_provinces()
        self.action_sync_cities()
        self.action_sync_districts()
        self.action_sync_villages()
        return self._notify('Indonesia Region Sync', 'Full region sync completed successfully.')
