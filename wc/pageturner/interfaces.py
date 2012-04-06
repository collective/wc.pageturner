from zope.interface import Interface
from wc.pageturner import mf as _
from zope import schema


class Layer(Interface):
    """
    layer class
    """


class IGlobalPageTurnerSettings(Interface):

    width = schema.Int(
        title=_(u'label_width_title_pageturner', default=u"Width"),
        description=_(u"label_width_description_pageturn",
            default=u"The fixed width of the Page Viewer."),
        default=650,
        required=True
    )

    height = schema.Int(
        title=_(u'label_height_title_pageturner', default=u"Height"),
        description=_(u"label_height_description_pageturner",
            default=u"The fixed height of the Page Viewer."),
        default=500,
        required=True
    )

    progressive_loading = schema.Bool(
        title=_(u'label_progressive_loading_pageturner',
            default=u'Progressive Loading'),
        description=_(u'label_progressive_loading_description_pageturner',
            default=u'Progressively load the PDF. Essential '
                    u'for very large PDF files.'),
        default=True,
        required=False
    )

    print_enabled = schema.Bool(
        title=_(u'label_print_enabled_pageturner', default=u'Print Enabled'),
        description=_(u'label_print_enabled_description_pageturner',
            default=u'Printer button enabled.'),
        default=True,
        required=False
    )

    fit_width_on_load = schema.Bool(
        title=_(u'label_fit_width_on_load_pageturner', default=u'Fit Width'),
        description=_(u'label_fit_width_on_load_description_pageturner',
            default=u'Should we scale to full width'),
        default=False,
        required=False
    )

    full_screen_visible = schema.Bool(
        title=_(u'label_full_screen_visible_pageturner',
            default=u'Full Screen Visible'),
        description=_(u'label_full_screen_visible_description_pageturner',
            default=u'Full screen button visible.'),
        default=True,
        required=False
    )

    search_tools_visible = schema.Bool(
        title=_(u'label_search_tools_visible_pageturner',
            default=u'Search Tools Visible'),
        description=_(u'label_search_tools_visible_description_pageturner',
            default=u'Search tools button visible.'),
        default=True,
        required=False
    )

    cursor_tools_visible = schema.Bool(
        title=_(u'label_cursor_tools_visible_pageturner',
            default=u'Cursor Tools Visible'),
        description=_(u'label_cursor_tools_visible_description_pageturner',
            default=u'Cursor tools button visible.'),
        default=True,
        required=False
    )

    command_line_options = schema.TextLine(
        title=_(u'label_command_line_options_pageturner',
            default=u'Command Line Options'),
        description=_(u'description_command_line_options_pageturner',
            default=u'It is possible that you need to provide extra options if'
                    u" there are errors while converting the PDF. "
                    u'This should be a comma seperated list of '
                    u'values(example "bitmap,bitmapfonts").'
                    u"""Some known helpful options are "poly2bitmap" """
                    u"""for bitmap errors and "bitmapfonts" """
                    u"""for bitmap font errors."""
        ),
        default=u'',
        required=False
    )


class IPageTurnerSettings(Interface):
    width = schema.Int(
        title=_(u'label_width_title_pageturner', default=u"Width"),
        description=_(u"label_width_description_pageturn",
            default=u"The fixed width of the Page Viewer."),
        default=None,
        required=False
    )

    height = schema.Int(
        title=_(u'label_height_title_pageturner', default=u"Height"),
        description=_(u"label_height_description_pageturner",
            default=u"The fixed height of the Page Viewer."),
        default=None,
        required=False
    )

    progressive_loading = schema.Bool(
        title=_(u'label_progressive_loading_pageturner',
            default=u'Progressive Loading'),
        description=_(u'label_progressive_loading_description_pageturner',
            default=u'Progressively load the PDF. '
                    u'Essential for very large PDF files.'),
        default=None,
        required=False
    )

    print_enabled = schema.Bool(
        title=_(u'label_print_enabled_pageturner', default=u'Print Enabled'),
        description=_(u'label_print_enabled_description_pageturner',
            default=u'Printer button enabled.'),
        default=None,
        required=False
    )

    fit_width_on_load = schema.Bool(
        title=_(u'label_fit_width_on_load_pageturner', default=u'Fit width'),
        description=_(u'label_fit_width_on_load_description_pageturner',
            default=u'Should the pages fit the width.'),
        default=None,
        required=False
    )

    full_screen_visible = schema.Bool(
        title=_(u'label_full_screen_visible_pageturner',
            default=u'Full Screen Visible'),
        description=_(u'label_full_screen_visible_description_pageturner',
            default=u'Full screen button visible.'),
        default=None,
        required=False
    )

    search_tools_visible = schema.Bool(
        title=_(u'label_search_tools_visible_pageturner',
            default=u'Search Tools Visible'),
        description=_(u'label_search_tools_visible_description_pageturner',
            default=u'Search tools button visible.'),
        default=None,
        required=False
    )

    cursor_tools_visible = schema.Bool(
        title=_(u'label_cursor_tools_visible_pageturner',
            default=u'Cursor Tools Visible'),
        description=_(u'label_cursor_tools_visible_description_pageturner',
            default=u'Cursor tools button visible.'),
        default=None,
        required=False
    )

    command_line_options = schema.TextLine(
        title=_(u'label_command_line_options_pageturner',
            default=u'Command Line Options'),
        description=_(u'description_command_line_options_pageturner',
            default=u'It is possible that you need to provide extra options '
                    u'if there are errors while converting the PDF. '
                    u'This should be a comma seperated list of '
                    u'values(example "bitmap,bitmapfonts").'
                    u"""Some known helpful options are "poly2bitmap" """
                    u"""for bitmap errors and "bitmapfonts" """
                    u"""for bitmap font errors."""
        ),
        default=None,
        required=False
    )

    encryption_password = schema.Password(
        title=_(u'label_password_pageturner', default=u'Encryption Password'),
        description=_(u'description_password_pageturner',
            default=u'Enter a password if your pdf is encrypted.'),
        default=u'',
        required=False
    )


class IUtils(Interface):

    def enabled():
        """
        return true is page turner is enabled for the object
        """

    def convert():
        """
        force conversion
        """
