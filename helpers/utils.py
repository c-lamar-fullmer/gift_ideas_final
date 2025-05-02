from flask import session

def parse_gift_list(gifts_str):
    """
    Parses a string containing a newline-separated list of gifts into a Python list.
    It splits the string by newline characters, strips any leading/trailing whitespace
    from each gift, and filters out any empty strings.
    """
    return [gift.strip() for gift in gifts_str.split('\n') if gift.strip()]

def sort_names(people_list):
    """
    Sorts a list of dictionaries representing people by their 'name' key.
    The sorting is done case-insensitively to ensure proper alphabetical order.
    """
    return sorted(people_list, key=lambda person: person['name'].lower())

def sort_gifts(gift_list):
    """
    Sorts a list of gift strings alphabetically.
    """
    return sorted(gift_list)