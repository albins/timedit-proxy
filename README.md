# What is this

The schedule output from TimeEdit at my university looks _awful_. To mitigate
this, I made an iCalendar proxy that would allow filtering and transformation of
calendar events.

## Usage

You need to write your rules in the file `filters.yaml`, like this:

```yaml
- type: all-day
  action: drop

- name: ".*"
  action: translate
  translate:
    name: "{{ name | regex_replace('.*, +(.*)\\. +, +(.*), (.*)', '\\\\1: \\\\2 (\\\\3)') }}"
```


You should be able to have multiple targets if you like (e.g. add the old name
to the description, then butcher the previous name).

Rules are evaluated top-to-bottom. Available fields are `name`, `location`, and
`description`. Templates are Jinja 2, with the `regex_replace` filter added.

Once the service is running, the REST endpoint `/calendar/` will receive a full
URL (`https://`` and all), e.g.
http://my-server/calendar/https://a-calendar.com/ics will give you the calendar
at https://a-calendar.com/ics, but filtered.

Nothing is authenticated. Yes, this is probably dangerous.
