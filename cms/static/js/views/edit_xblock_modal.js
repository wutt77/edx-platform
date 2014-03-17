define(["jquery", "underscore", "underscore.string", "gettext", "js/views/baseview", "js/views/xblock", "js/models/xblock_info"],
    function($, _, str, gettext, BaseView, XBlockView, XBlockInfo) {
        var EditXBlockModal = BaseView.extend({
            events : {
                "click .action-add": "add",
                "click .action-cancel": "cancel"
            },

            options: $.extend({}, BaseView.prototype.options, {
                type: "prompt",
                closeIcon: false,
                icon: false
            }),

            initialize: function() {
                var collection;
                this.template = _.template($("#edit-xblock-modal-tpl").text());
            },

            render: function() {
                var xblockView,
                    model,
                    wrapperXBlock = this.wrapperXBlock,
                    locator = wrapperXBlock.data('locator');
                this.$el.html(this.template());
                model = new XBlockInfo({
                    "category": "vertical",
                    "display-name": "A/B Test",
                    "id": locator
                });
                xblockView = new XBlockView({
                    el: this.$('.xblock-editor'),
                    model: model,
                    view: 'studio_view'
                });
                xblockView.render();
            },

            cancel: function(event) {
                event.preventDefault();
                this.hide();
            },

            show: function() {
                $('body').addClass('dialog-is-shown');
                this.$('.wrapper-dialog-edit-xblock').addClass('is-shown');
            },

            hide: function() {
                $('body').removeClass('dialog-is-shown');
                this.$('.wrapper-dialog-edit-xblock').removeClass('is-shown');
            }
        });

        return EditXBlockModal;
    });
