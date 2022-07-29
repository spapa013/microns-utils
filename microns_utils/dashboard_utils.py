from traitlets import Unicode, Dict, Unicode
from ipywidgets import DOMWidget, register, link
import wridgets.app as wra

jupyerhub_get_user_info = """
    require.undef('user_widget');

    define('user_widget', ["@jupyter-widgets/base"], function (widgets) {

        
        var UserView = widgets.DOMWidgetView.extend({
            initialize: function(attributes, options) {

            this.response = fetch(
                    '/hub/dashboards-api/hub-info/user',
                    { 
                    mode: 'no-cors', 
                    credentials: 'same-origin',
                    headers: new Headers({'Access-Control-Allow-Origin':'*'}) 
                });
                this.response.then( response => {
                    this.result = response.json();
                    this.result.then( json => {
                        this.model.set('value', json);
                        this.model.set('name', json.name);
                        this.model.save_changes();
                    });

                });
            
            },
            
            render: async function () {
                await this.response;
                await this.result;
                var json = this.model.get('value');
                var text = 'No user';
                if (json.hasOwnProperty('name')) {
                    text = '';
                }
                this.el.appendChild(document.createTextNode(text));

            },
        
        });

        return {
            UserView: UserView
        };
    });
    """

@register
class DashboardUser(DOMWidget):
    """
    Get JupyterHub user info
    https://gist.github.com/danlester/ac1d5f29358ce1950482f8e7d4301f86
    """
    _view_name = Unicode('UserView').tag(sync=True)
    _view_module = Unicode('user_widget').tag(sync=True)
    _view_module_version = Unicode('0.1.0').tag(sync=True)

    value = Dict({}, help="User info").tag(sync=True)
    name = Unicode('').tag(sync=True)


class UserApp(wra.App):
    store_config = [
        'user',
        'user_info'
        'user_app'
    ]
    
    def make(self, **kwargs):
        self.propagate = True
        
        self.core = (
            wra.Label(text='User', name='UserLabel') + \
            wra.Field(disabled=True, name='UserField')
        )
        
        if 'user_app' in kwargs:
            self.user_app = kwargs.get('user_app')
            link((self.children.UserField.wridget.widget, 'value'), (self.user_app, 'name'))
            
        elif 'user_info' in kwargs:
            self.user_info = kwargs.get('user_info')
            self.user = self.user_info.get('name')
            self.children.UserField.set(value=self.user)
            
    def set_user_from_user_app(self):
        assert self.user_app is not None, 'Cant set user_info because user_app is None'
        self.user = self.user_app.value.get('name')
        self.user_info = self.user_app.value