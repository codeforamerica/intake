"""A utility module turning English into machine-readable data."""


def oxford_comma_text_to_list(phrase):
    """Examples:
    - 'Eeeny, Meeny, Miney, and Moe' --> ['Eeeny', 'Meeny', 'Miney', 'Moe']
    - 'Black and White' --> ['Black', 'White']
    - 'San Francisco and Saint Francis' -->
        ['San Francisco', 'Saint Francisco']
    """
    items = []
    for subphrase in phrase.split(', '):
        items.extend(
            [item.strip() for item in subphrase.split(' and ')])
    return items
