import tinycss

from .rules import FontFaceRule


class CSSParser(tinycss.CSSPage3Parser):

    def parse_at_rule(self, rule, previous_rules, errors, context):

        if rule.at_keyword == '@font-face':
            declarations, errors = self.parse_declaration_list(rule.body)
            errors.extend(errors)
            return FontFaceRule(declarations, rule.line, rule.column)

        return super(CSSParser, self).parse_at_rule(
            rule, previous_rules, errors, context)
