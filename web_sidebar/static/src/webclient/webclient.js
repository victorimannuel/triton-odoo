import { patch } from '@web/core/utils/patch';

import { WebClient } from '@web/webclient/webclient';
import { SideBar } from '@web_sidebar/webclient/sidebar/sidebar';

patch(WebClient, {
    components: {
        ...WebClient.components,
        SideBar,
    },
});
