from flask import session

def parse_gift_list(gifts_str):
    # Parse the string into a list of gifts
    return [gift.strip() for gift in gifts_str.split('\n') if gift.strip()]

def sort_names(people_list):
    # Sorts a list of dictionaries by the 'name' key, case-insensitive manner
    return sorted(people_list, key=lambda person: person['name'].lower())

def sort_gifts(gift_list):
    # Sorts the list of gifts alphabetically
    return sorted(gift_list)