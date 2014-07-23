
class FontFaceRule(object):
    """
    @font-face rule
    """
    at_keyword = '@font-face'

    def __init__(self, declarations, line, column):
        self.declarations = declarations
        self.line = line
        self.column = column
