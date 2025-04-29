from flask import session

def parse_gift_list(gifts_str):
    return [gift.strip() for gift in gifts_str.split('\n') if gift.strip()]

def sort_names(people_list):
    return sorted(people_list, key=lambda person: person['name'].lower())

def sort_gifts(gift_list):
    return sorted(gift_list)
