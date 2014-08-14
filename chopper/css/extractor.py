import re
import cssselect
from six.moves.urllib.parse import urljoin
from tinycss.css21 import RuleSet, ImportRule, MediaRule, PageRule
from tinycss.parsing import split_on_comma, strip_whitespace

from .parser import CSSParser
from .rules import FontFaceRule
from .translator import XpathTranslator

from ..mixins import TreeBuilderMixin


class CSSExtractor(TreeBuilderMixin):
    """
    Extracts CSS rules only matching a html tree
    """
    parser = CSSParser()
    xpath_translator = XpathTranslator()

    rel_to_abs_re = re.compile(
        r'url\(["\']?(?!data:)(?P<path>[^\)]*)["\']?\)',
        re.IGNORECASE | re.MULTILINE)

    def __init__(self, css_contents, html_contents):
        """
        Inits the CSS extractor

        :param css_contents: The CSS contents to parse
        :type css_contents: str
        :param html_contents: The HTML contents to parse
        :type html_contents: str
        """
        self.css_contents = css_contents
        self.html_contents = html_contents
        self.cleaned_css = ''

    ##########
    # Public #
    ##########

    def parse(self):
        """
        Parses the CSS contents and returns the cleaned CSS as a string

        :returns: The cleaned CSS
        :rtype: str
        """
        # Build the HTML tree
        self.tree = self._build_tree(self.html_contents)

        # Parse the CSS contents
        self.stylesheet = self.parser.parse_stylesheet(self.css_contents)

        # Get the cleaned CSS contents
        self.cleaned_css = self._clean_css()

    def rel_to_abs(self, base_url):
        """
        Converts relative links from css contents to absolute links

        :param base_url: The base page url to use for building absolute links
        :type base_url: str
        :param css_contents: The CSS contents to parse
        :type css_contents: str
        """
        self.cleaned_css = self.rel_to_abs_re.sub(
            lambda match: "url('%s')" % urljoin(
                base_url, match.group('path').strip('\'"')),
            self.cleaned_css)

    def to_string(self):
        """
        Returns the cleaned CSS as a string

        :returns: The cleaned CSS contents
        :rtype: str
        """
        return self.cleaned_css

    ###########
    # Private #
    ###########

    def _clean_css(self):
        """
        Returns the cleaned CSS

        :param stylesheet: The Stylesheet object to parse
        :type stylesheet: tinycss.css21.Stylesheet
        """
        # Init the cleaned CSS rules and contents string
        css_rules = []

        # For every rule in the CSS
        for rule in self.stylesheet.rules:

            try:
                # Clean the CSS rule
                cleaned_rule = self._clean_rule(rule)

                # Append the rule to matched CSS rules
                if cleaned_rule is not None:
                    css_rules.append(cleaned_rule)

            except:
                # On error, assume the rule matched the tree
                css_rules.append(rule)

        return self._build_css(css_rules)

    def _clean_rule(self, rule):
        """
        Cleans a css Rule by removing Selectors without matches on the tree
        Returns None if the whole rule do not match

        :param rule: CSS Rule to check
        :type rule: A tinycss Rule object
        :returns: A cleaned tinycss Rule with only Selectors matching the tree or None
        :rtype: tinycss Rule or None
        """
        # Always match @ rules
        if rule.at_keyword is not None:
            return rule

        # Clean selectors
        cleaned_token_list = []

        for token_list in split_on_comma(rule.selector):

            # If the token list matches the tree
            if self._token_list_matches_tree(token_list):

                # Add a Comma if multiple token lists matched
                if len(cleaned_token_list) > 0:
                    cleaned_token_list.append(
                        cssselect.parser.Token('DELIM', ',', len(cleaned_token_list) + 1))

                # Append it to the list of cleaned token list
                cleaned_token_list += token_list

        # Return None if selectors list is empty
        if not cleaned_token_list:
            return None

        # Update rule token list
        rule.selector = cleaned_token_list

        # Return cleaned rule
        return rule

    def _token_list_matches_tree(self, token_list):
        """
        Returns whether the token list matches the HTML tree

        :param selector: A Token list to check
        :type selector: list of Token objects
        :returns: True if the token list has matches in self.tree
        :rtype: bool
        """
        try:
            parsed_selector = cssselect.parse(
                ''.join(token.as_css() for token in token_list))[0]

            return bool(
                self.tree.xpath(
                    self.xpath_translator.selector_to_xpath(parsed_selector)))
        except:
            # On error, assume the selector matches the tree
            return True

    def _build_css(self, rules):
        """
        Returns a CSS string for the given rules

        :param rules: List of tinycss Rule
        :type rules: list of tinycss Rule objects
        :returns: CSS contents for the rules
        :rtype: string
        """
        # Build and return the cleaned CSS contents
        return '\n'.join(self._rule_as_string(rule) for rule in rules)

    def _rule_as_string(self, rule):
        """
        Converts a tinycss rule to a formatted CSS string

        :param rule: The rule to format
        :type rule: tinycss Rule object
        :returns: The Rule as a CSS string
        :rtype: str
        """
        if isinstance(rule, RuleSet):
            # Simple CSS rule : a { color: red; }
            return '%s{%s}' % (
                self._selector_as_string(rule.selector),
                self._declarations_as_string(rule.declarations))

        elif isinstance(rule, ImportRule):
            # @import rule
            return "@import url('%s') %s;" % (
                rule.uri, ','.join(rule.media))

        elif isinstance(rule, FontFaceRule):
            # @font-face rule
            return "@font-face{%s}" % self._declarations_as_string(rule.declarations)

        elif isinstance(rule, MediaRule):
            # @media rule
            return "@media %s{%s}" % (
                ','.join(rule.media),
                ''.join(self._rule_as_string(r) for r in rule.rules))

        elif isinstance(rule, PageRule):
            # @page rule
            selector, pseudo = rule.selector

            return "@page%s%s{%s}" % (
                ' %s' % selector if selector else '',
                ' :%s' % pseudo if pseudo else '',
                self._declarations_as_string(rule.declarations))

        return ''

    def _selector_as_string(self, selector):
        """
        Returns a selector as a CSS string

        :param selector: A list of tinycss Tokens
        :type selector: list
        :returns: The CSS string for the selector
        :rtype: str
        """
        return ','.join(
            ''.join(token.as_css() for token in strip_whitespace(token_list))
            for token_list in split_on_comma(selector))

    def _declarations_as_string(self, declarations):
        """
        Returns a list of declarations as a formatted CSS string

        :param declarations: The list of tinycss Declarations to format
        :type declarations: list of tinycss.css21.Declaration
        :returns: The CSS string for the declarations list
        :rtype: str
        """
        return ''.join('%s:%s;' % (d.name, d.value.as_css()) for d in declarations)
