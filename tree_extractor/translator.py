from cssselect import HTMLTranslator


class XpathTranslator(HTMLTranslator):
    """
    Custom xpath translator
    """
    def pseudo_matches_if_exists(self, xpath):
        """
        Returns the default xpath
        """
        return xpath

    xpath_link_pseudo = pseudo_matches_if_exists
    xpath_visited_pseudo = pseudo_matches_if_exists
    xpath_hover_pseudo = pseudo_matches_if_exists
    xpath_active_pseudo = pseudo_matches_if_exists
    xpath_focus_pseudo = pseudo_matches_if_exists
    xpath_target_pseudo = pseudo_matches_if_exists
    xpath_enabled_pseudo = pseudo_matches_if_exists
    xpath_disabled_pseudo = pseudo_matches_if_exists
    xpath_checked_pseudo = pseudo_matches_if_exists
