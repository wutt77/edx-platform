define(["jquery", "underscore", "underscore.string", "gettext", "js/views/baseview",
    "js/views/xblock", "js/models/xblock_info", "js/views/metadata", "js/collections/metadata"],
    function($, _, str, gettext, BaseView, XBlockView, XBlockInfo, MetadataView, MetadataCollection) {
        var EditXBlockModal = BaseView.extend({
            events : {
                "click .action-add": "add",
                "click .action-cancel": "cancel",
                "click .action-modes a": "changeMode"
            },

            mode: 'editor-mode',

            options: $.extend({}, BaseView.prototype.options, {
                type: "prompt",
                closeIcon: false,
                icon: false
            }),

            initialize: function() {
                this.template = _.template($("#edit-xblock-modal-tpl").text());
            },

            render: function(options) {
                var self = this,
                    editorView,
                    xblockInfo = this.xblockInfo,
                    success = options ? options.success : null;
                this.$el.html(this.template());
                editorView = new XBlockView({
                    el: this.$('.xblock-editor'),
                    model: xblockInfo,
                    view: 'studio_view'
                });
                this.editorView = editorView;
                editorView.render({
                    success: function() {
                        if (success) {
                            success();
                        }
                        self.createMetadataView();
                    }
                });
            },

            createMetadataView: function() {
                var metadataEditor = this.$('.metadata_edit'),
                    metadataData = metadataEditor.data('metadata'),
                    models = [],
                    key,
                    xblock = this.editorView.xblock;
                for (key in metadataData) {
                    if (metadataData.hasOwnProperty(key)) {
                        models.push(metadataData[key]);
                    }
                }
                this.settingsView = new MetadataView.Editor({
                    el: metadataEditor,
                    collection: new MetadataCollection(models)
                });
                if (xblock.setMetadataEditor) {
                    xblock.setMetadataEditor(this.settingsView);
                }
                if (this.hasDataEditor()) {
                    this.selectMode('editor');
                } else {
                    this.selectMode('settings');
                }
            },

            hasDataEditor: function() {
                return this.$('.wrapper-comp-editor').length > 0;
            },

            changeMode: function(event) {
                var parent = $(event.target.parentElement),
                    mode = parent.data('mode');
                event.preventDefault();
                this.selectMode(mode);
            },

            selectMode: function(mode) {
                var showEditor = mode === 'editor',
                    editorView = this.editorView,
                    settingsView = this.settingsView;
                if (showEditor) {
                    editorView.$el.show();
                    settingsView.$el.hide();
                } else {
                    settingsView.$el.show();
                    editorView.$el.hide();
                }
            },

            cancel: function(event) {
                event.preventDefault();
                this.hide();
            },

            edit: function(event, rootXBlockInfo) {
                var self = this,
                    dataElement = $(event.target).closest('[data-locator]');
                event.preventDefault();
                this.xblockInfo = this.findXBlockInfo(event, rootXBlockInfo);
                this.render({
                    success: _.bind(this.show, this)
                });
            },

            findXBlockInfo: function(event, defaultXBlockInfo) {
                var self = this,
                    dataElement = $(event.target).closest('[data-locator]'),
                    xblockInfo = defaultXBlockInfo;
                if (dataElement.length > 0) {
                    xblockInfo = new XBlockInfo({
                        'id': dataElement.data('locator'),
                        'display-name': dataElement.data('display-name'),
                        'category': dataElement.data('category')
                    });
                }
                return xblockInfo;
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
