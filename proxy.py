#!/usr/bin/env python3
import re

import flask
import ics
import jinja2
import requests
import yaml

URL = "https://cloud.timeedit.net/uu/web/schema/ri6XZ0g74560Y7QQ4YZ6800Y05y000Q6n5d51Q684v573ZQ0Z3Q5t134B4F981D24B00tD818C5DQ57E4A6909A03ZFE7.ics"

NAME_TEMPLATE = "{{ name | regex_replace('.*, +(.*)\\. +, +(.*), (.*)', '\\\\1: \\\\2 (\\\\3)') }}"

EVENT_FIELDS = ["location", "name", "description"]


# Custom filter method
def regex_replace(s, find, replace):
    result = re.sub(find, replace, s)

    return result


def match_all(_e):
    return True


def event_to_params(event):
    return {f: getattr(event, f) for f in EVENT_FIELDS}


def rule_to_transform_fn(rule):
    if rule['action'] == 'drop':
        return lambda e: None

    translations = rule['translate']
    environment = jinja2.Environment()
    environment.filters['regex_replace'] = regex_replace

    templates = {
        field: environment.from_string(translations[field])
        if field in translations else None
        for field in EVENT_FIELDS
    }

    def transform(event):
        new_event = event
        for field, template in templates.items():
            if not template:
                continue
            new_value = template.render(**event_to_params(new_event))
            setattr(new_event, field, new_value)
        return new_event

    return transform


def name_matcher(rule):
    if not 'name' in rule:
        return match_all

    return lambda e: re.match(rule['name'], e.name)


def type_matcher(rule):
    if not 'type' in rule:
        return match_all
    if rule['type'] == "all-day":
        return lambda e: e.all_day
    raise Exception

    return match_all


def rule_to_matcher_fn(rule):
    matchers = [name_matcher(rule), type_matcher(rule)]
    return lambda event: all([matcher(event) for matcher in matchers])


def rule_to_fn(rule):
    matches = rule_to_matcher_fn(rule)
    do_transform = rule_to_transform_fn(rule)

    def rule(event):
        return do_transform(event) if matches(event) else event

    return rule


def filter_event(event, filters):
    for f in filters:
        event = f(event)
        if event is None:
            return None

    return event


def apply_filters(calendar, filters):
    filtered_calendar = ics.Calendar()
    for event in calendar.events:
        filtered_event = filter_event(event, filters)
        if not filtered_event:
            continue

        filtered_calendar.events.add(filtered_event)

    return filtered_calendar


def main():
    c = ics.Calendar(requests.get(URL).text)
    with open("filters.yaml", "r") as f:
        rules = yaml.load(f)

    filters = [rule_to_fn(rule) for rule in rules]

    for event in apply_filters(c, filters).events:
        print("{} in {} starts {}".format(event.name, event.location,
                                          event.begin.humanize()))


if __name__ == '__main__':
    main()
