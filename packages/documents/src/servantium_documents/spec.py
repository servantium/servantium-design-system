"""The deck spec: what Claude writes instead of Python.

A spec is YAML because speaker notes are long prose, but it is loaded strictly and
validated against a JSON Schema, so YAML's loose typing cannot slip through (a bare
`no` becoming False, a date becoming a datetime).

Shape:

    deck: Status Report            # the deck's name, used in the file name
    client: Acme                   # the customer folder; "_Sandbox" for tests
    date: 2026-09-29               # optional, defaults to today
    slides:
      - cover:   {eyebrow, title, subtitle, meta}
      - section: {number, title, lede}
      - content: {eyebrow, title, lede, body: [component, ...], source, notes}
      - bullets: {eyebrow, title, lede, points: [...], source, notes}
      - columns: {eyebrow, title, lede, left: [...], right: [...], source, notes}
      - comparison: {eyebrow, title, lede, left: {heading, points}, right: {heading, points}}
      - numbers: {eyebrow, title, lede, stats: [{value, label}] x3, source, notes}
      - quote:   {text, attribution, notes}
      - picture: {eyebrow, title, points, image, source, notes}
      - closing: {title, asks: [...], cta, notes}

Every slide and every component is a one-key mapping, so the file reads top to
bottom like the storyboard it came from.
"""
import datetime as dt
import hashlib
import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

# ── components: the 2-3-4 rule lives in minItems/maxItems ────────────────────
S = {'type': 'string', 'minLength': 1}
LINES = {'type': 'array', 'items': S, 'maxItems': 4}


def _list(item, lo=2, hi=4):
    return {'type': 'array', 'items': item, 'minItems': lo, 'maxItems': hi}


def _obj(props, required=()):
    return {'type': 'object', 'properties': props, 'required': list(required), 'additionalProperties': False}


PILL_TONES = ('green', 'forest', 'mint', 'amber', 'coral', 'slate', 'cloud')
GRID_TONES = ('green', 'forest', 'mint', 'amber', 'slate', 'cloud', 'teal', 'coral')
_CAP_SIDE = _obj({'label': S, 'tone': {'enum': ['warn', 'good']},
                  'blocks': {'type': 'array', 'minItems': 1, 'maxItems': 5, 'items': _obj({
                      'label': S, 'amount': S, 'value': {'type': 'number'}}, ['label'])},
                  'lines': LINES}, ['label', 'blocks'])


COMPONENTS = {
    'cards': _list(_obj({'icon': S, 'title': S, 'lines': LINES, 'kicker': S}, ['title'])),
    'tiles': _list(_obj({'icon': S, 'label': S}, ['icon', 'label'])),
    'stats': _list(_obj({'value': S, 'label': S, 'note': S}, ['value', 'label'])),
    'steps': _list(_obj({'lead': S, 'text': S}, ['lead', 'text'])),
    'timeline': _list(_obj({'icon': S, 'when': S, 'focus': S, 'moves': S,
                            'focus_label': S, 'moves_label': S}, ['icon', 'when', 'focus', 'moves'])),
    'chevrons': _list(_obj({'stage': S, 'question': S, 'text': S}, ['stage', 'question', 'text'])),
    'milestones': _list(_obj({'icon': S, 'when': S, 'title': S, 'text': S, 'done': {'type': 'boolean'}},
                             ['when', 'title', 'text'])),
    'panels': _list(_obj({'icon': S, 'title': S, 'tag': S, 'tone': {'enum': ['green', 'amber']}, 'lines': LINES},
                         ['title', 'lines']), 2, 2),
    'compare': _obj({'before': _obj({'label': S, 'icon': S, 'lines': LINES}, ['label', 'lines']),
                     'after': _obj({'label': S, 'icon': S, 'lines': LINES}, ['label', 'lines'])}, ['before', 'after']),
    'shipped': _obj({'groups': {'type': 'array', 'minItems': 2, 'maxItems': 4, 'items': _obj({
                        'title': S, 'items': {'type': 'array', 'minItems': 2, 'maxItems': 7,
                                              'items': _obj({'icon': S, 'label': S}, ['label'])}},
                        ['title', 'items'])}}, ['groups']),
    'chain': _list(_obj({'icon': S, 'title': S, 'text': S}, ['icon', 'title', 'text'])),
    'logos': _list(_obj({'logo': S, 'title': S, 'text': S}, ['logo', 'title', 'text'])),
    'people': _list(_obj({'photo': S, 'name': S, 'role': S, 'lines': {'type': 'array', 'items': S, 'maxItems': 3},
                          'logos': {'type': 'array', 'items': S, 'maxItems': 4}}, ['photo', 'name', 'role']), 2, 3),
    'hub': _obj({'left': _list(_obj({'name': S, 'icon': S, 'logo': S}, ['name'])),
                 'right': _list(_obj({'name': S, 'icon': S, 'logo': S}, ['name'])),
                 'left_label': S, 'right_label': S,
                 'top': _obj({'title': S, 'text': S, 'icon': S}, ['title']),
                 'bottom': _obj({'title': S, 'text': S, 'icon': S}, ['title']),
                 'caption': S}, ['left', 'right']),
    # Named exceptions to 2-3-4: their structure carries the meaning.
    'table': _obj({'head': {'type': 'array', 'items': S, 'minItems': 2, 'maxItems': 6},
                   'rows': {'type': 'array', 'items': {'type': 'array', 'items': {'type': 'string'}},
                            'minItems': 1, 'maxItems': 10},
                   'widths': {'type': 'array', 'items': {'type': 'number'}},
                   'row_h': {'type': 'number'},
                   'pills': {'type': 'array', 'maxItems': 3, 'items': _obj({
                       'column': {'type': 'integer', 'minimum': 1},
                       'tones': {'type': 'object', 'additionalProperties': {
                           'enum': ['green', 'forest', 'mint', 'amber', 'coral', 'slate', 'cloud']}}},
                       ['column', 'tones'])}}, ['head', 'rows']),
    'diagram': _obj({'mermaid': S, 'height': {'type': 'number'}}, ['mermaid']),
    'chart': _obj({'type': {'enum': ['column', 'bar', 'stacked', 'line']},
                   'categories': {'type': 'array', 'items': S, 'minItems': 2, 'maxItems': 12},
                   'series': {'type': 'array', 'minItems': 1, 'maxItems': 4,
                              'items': _obj({'name': S, 'values': {'type': 'array', 'items': {'type': 'number'}}},
                                            ['name', 'values'])},
                   'unit': S, 'format': S, 'height': {'type': 'number'}}, ['type', 'categories', 'series']),
    'image': _obj({'path': S, 'height': {'type': 'number'}, 'frame': {'type': 'boolean'}}, ['path']),
    # Plan and flow pictures (named exceptions: their structure carries the meaning).
    'gantt': _obj({'periods': {'type': 'array', 'items': S, 'minItems': 2, 'maxItems': 16},
                   'rows': {'type': 'array', 'minItems': 1, 'maxItems': 8, 'items': _obj({
                       'name': S, 'note': S,
                       'bars': {'type': 'array', 'minItems': 0, 'maxItems': 6, 'items': _obj({
                           'from': {'type': 'integer', 'minimum': 1}, 'to': {'type': 'integer', 'minimum': 1},
                           'label': S, 'tone': {'enum': ['green', 'forest', 'amber', 'mint', 'slate']}},
                           ['from', 'to', 'label'])}}, ['name', 'bars'])},
                   'gates': {'type': 'array', 'maxItems': 6, 'items': _obj({
                       'after': {'type': 'number'}, 'label': S}, ['after', 'label'])}},
                  ['periods', 'rows']),
    'flow': _obj({'steps': {'type': 'array', 'items': S, 'minItems': 2, 'maxItems': 6},
                  'active': {'type': 'integer', 'minimum': 1},
                  'inputs': {'type': 'array', 'minItems': 1, 'maxItems': 4, 'items': _obj({
                      'icon': S, 'logo': S, 'title': S, 'meta': S, 'tag': S, 'carried': {'type': 'boolean'}}, ['title', 'meta'])},
                  'node': _obj({'title': S, 'verb': S, 'chip': S,
                                'cycle': {'type': 'array', 'items': S, 'minItems': 2, 'maxItems': 2}}, ['title', 'verb']),
                  'output': _obj({'label': S, 'ref': S, 'title': S, 'foot': S,
                                  'rows': {'type': 'array', 'minItems': 1, 'maxItems': 5, 'items': _obj({
                                      'key': S, 'text': S, 'open': {'type': 'boolean'}}, ['key', 'text'])}},
                                 ['label', 'title', 'rows'])},
                 ['inputs', 'node', 'output']),
    'swimlane': _obj({
        'lanes': {'type': 'array', 'minItems': 2, 'maxItems': 5,
                  'items': _obj({'key': S, 'name': S, 'note': S}, ['key', 'name'])},
        'steps': {'type': 'array', 'minItems': 2, 'maxItems': 12, 'items': _obj({
            'id': {'type': ['string', 'integer']}, 'num': {'type': ['string', 'integer']},
            'lane': S, 'lanes': {'type': 'array', 'items': S, 'minItems': 2, 'maxItems': 3},
            'title': S, 'text': S, 'target': S, 'icon': S, 'branch': {'type': 'boolean'},
            'kind': {'enum': ['task', 'call', 'optional', 'approval', 'end']}}, ['id', 'title'])},
        'loops': {'type': 'array', 'maxItems': 4, 'items': _obj({
            'from': {'type': ['string', 'integer']}, 'to': {'type': ['string', 'integer']}, 'label': S},
            ['from', 'to'])},
        'phases': {'type': 'array', 'maxItems': 6, 'items': _obj({
            'label': S, 'from': {'type': ['string', 'integer']}, 'to': {'type': ['string', 'integer']}},
            ['label', 'from', 'to'])},
        'clock': S}, ['lanes', 'steps']),
    'stack': _obj({'tiers': {'type': 'array', 'minItems': 1, 'maxItems': 3, 'items': _obj({
                       'label': S, 'note': S,
                       'items': {'type': 'array', 'minItems': 2, 'maxItems': 6,
                                 'items': _obj({'name': S, 'icon': S, 'logo': S}, ['name'])}}, ['label', 'items'])},
                   'foundation': _obj({'title': S, 'text': S,
                                       'chips': {'type': 'array', 'items': S, 'minItems': 2, 'maxItems': 8}},
                                      ['title', 'chips'])},
                  ['tiers', 'foundation']),
    # Consulting pictures with their own shape (named exceptions: structure carries meaning).
    'adoption': _obj({'here': S, 'note': S,
                      'labels': {'type': 'array', 'items': S, 'minItems': 5, 'maxItems': 5}}, ['here']),
    'approach': _obj({'stages': {'type': 'array', 'items': S, 'minItems': 3, 'maxItems': 7},
                      'active': {'type': 'integer', 'minimum': 1},
                      'rows': {'type': 'array', 'minItems': 1, 'maxItems': 4, 'items': _obj({
                          'label': S, 'tone': {'enum': ['plain', 'record', 'ai', 'dark']},
                          'cells': {'type': 'array', 'items': S, 'minItems': 3, 'maxItems': 7}},
                          ['label', 'cells'])}}, ['stages', 'rows']),
    'zoom': _obj({'steps': {'type': 'array', 'items': S, 'minItems': 3, 'maxItems': 7},
                  'active': {'type': 'integer', 'minimum': 1}, 'title': S, 'meta': S, 'foot': S,
                  'rows': {'type': 'array', 'minItems': 2, 'maxItems': 5,
                           'items': _obj({'key': S, 'title': S, 'text': S}, ['title'])}},
                 ['steps', 'active', 'title', 'rows']),
    # Access or capability that widens one proven step at a time (3-5 steps, rising).
    'staircase': _obj({'steps': {'type': 'array', 'minItems': 3, 'maxItems': 5, 'items': _obj({
                           'label': S, 'title': S, 'text': S, 'when': S}, ['title'])},
                       'here': {'type': 'integer', 'minimum': 1}, 'here_label': S,
                       'numbered': {'type': 'boolean'}}, ['steps']),
    # A system in the middle, built outward: live in the center, each side's items with when they land.
    'middleout': _obj({'center': _obj({'title': S, 'note': S,
                                       'items': {'type': 'array', 'items': S, 'minItems': 2, 'maxItems': 5}},
                                      ['title', 'items']),
                       'left': _obj({'label': S, 'items': {'type': 'array', 'minItems': 2, 'maxItems': 4, 'items': _obj({
                           'icon': S, 'logo': S, 'name': S, 'text': S, 'when': S}, ['name'])}}, ['label', 'items']),
                       'right': _obj({'label': S, 'items': {'type': 'array', 'minItems': 2, 'maxItems': 4, 'items': _obj({
                           'icon': S, 'logo': S, 'name': S, 'text': S, 'when': S}, ['name'])}}, ['label', 'items'])},
                      ['center', 'left', 'right']),
    # A whole business on one page: numbered steps, what each covers (live, build, later), what it replaces.
    'processmap': _obj({'stages': {'type': 'array', 'minItems': 3, 'maxItems': 9, 'items': _obj({
                            'title': S, 'text': S,
                            'live': {'type': 'array', 'items': S, 'maxItems': 4},
                            'build': {'type': 'array', 'items': S, 'maxItems': 4},
                            'later': {'type': 'array', 'items': S, 'maxItems': 4},
                            'replaces': {'type': 'array', 'items': S, 'maxItems': 2}}, ['title'])},
                        'groups': {'type': 'array', 'maxItems': 4, 'items': _obj({
                            'label': S, 'from': {'type': 'integer', 'minimum': 1}, 'to': {'type': 'integer', 'minimum': 1},
                            'tone': {'enum': ['sales', 'live', 'plain']}}, ['label', 'from', 'to'])},
                        'loop': S}, ['stages']),
    # A pipeline board: sources feeding stage columns with example cards.
    'board': _obj({'sources': {'type': 'array', 'items': S, 'maxItems': 6}, 'sources_label': S,
                   'columns': {'type': 'array', 'minItems': 3, 'maxItems': 6, 'items': _obj({
                       'title': S, 'cards': {'type': 'array', 'maxItems': 3, 'items': _obj({
                           'title': S, 'meta': S, 'score': S, 'tag': S}, ['title'])}}, ['title'])}},
                  ['columns']),
    # Proposal and plan shapes (2026-10-20), so a long proposal never repeats a composition.
    # An inventory: groups as columns with a status pill, items as chips.
    'catalog': _obj({'groups': {'type': 'array', 'minItems': 2, 'maxItems': 8, 'items': _obj({
                         'title': S, 'tag': S, 'tone': {'enum': list(PILL_TONES)},
                         'items': {'type': 'array', 'items': S, 'minItems': 1, 'maxItems': 8}}, ['title', 'items'])}},
                    ['groups']),
    # Choices on one axis between two extremes, the recommended one lit.
    'spectrum': _obj({'left': S, 'right': S, 'pick_label': S,
                      'stops': {'type': 'array', 'minItems': 2, 'maxItems': 4, 'items': _obj({
                          'title': S, 'text': S, 'pick': {'type': 'boolean'}}, ['title'])}},
                     ['left', 'right', 'stops']),
    # The ways in, drawn as doors; the recommended one lit.
    'options': _obj({'pick_label': S, 'items': {'type': 'array', 'minItems': 2, 'maxItems': 4, 'items': _obj({
                         'label': S, 'title': S, 'meta': S, 'lines': LINES, 'pick': {'type': 'boolean'}}, ['title'])}},
                    ['items']),
    # Options compared on the same questions; cells can carry a 0-4 meter.
    'matrix': _obj({'columns': {'type': 'array', 'items': S, 'minItems': 2, 'maxItems': 4},
                    'highlight': {'type': 'integer', 'minimum': 1}, 'pick_label': S,
                    'rows': {'type': 'array', 'minItems': 2, 'maxItems': 7, 'items': _obj({
                        'label': S, 'cells': {'type': 'array', 'items': S, 'minItems': 2, 'maxItems': 4},
                        'levels': {'type': 'array', 'items': {'type': 'integer', 'minimum': 0, 'maximum': 4},
                                   'minItems': 2, 'maxItems': 4}}, ['label', 'cells'])}},
                   ['columns', 'rows']),
    # Spend stacked against a budget cap: phases priced one by one (unknowns dashed) vs one capped block.
    'cap': _obj({'cap': _obj({'value': {'type': 'number'}, 'label': S}, ['value', 'label']),
                 'left': _CAP_SIDE, 'right': _CAP_SIDE}, ['cap', 'left', 'right']),
    # A short plan at cell level: rows by periods, each cell coloured by its stage.
    'weekgrid': _obj({'periods': {'type': 'array', 'items': S, 'minItems': 2, 'maxItems': 16},
                      'stages': {'type': 'array', 'minItems': 2, 'maxItems': 7, 'items': _obj({
                          'key': S, 'label': S, 'short': S, 'tone': {'enum': list(GRID_TONES)}}, ['key', 'label'])},
                      'rows': {'type': 'array', 'minItems': 1, 'maxItems': 8, 'items': _obj({
                          'name': S, 'note': S, 'spans': {'type': 'array', 'maxItems': 8, 'items': _obj({
                              'from': {'type': 'integer', 'minimum': 1}, 'to': {'type': 'integer', 'minimum': 1},
                              'stage': S, 'label': S}, ['from', 'to', 'stage'])}}, ['name', 'spans'])},
                      'marks': {'type': 'array', 'maxItems': 6, 'items': _obj({
                          'at': {'type': 'integer', 'minimum': 1}, 'label': S}, ['at', 'label'])}},
                     ['periods', 'stages', 'rows']),
    # Lanes by period with cards in each cell: a month-by-month plan.
    'roadmap': _obj({'periods': {'type': 'array', 'items': S, 'minItems': 2, 'maxItems': 6},
                     'lanes': {'type': 'array', 'minItems': 2, 'maxItems': 5, 'items': _obj({
                         'name': S, 'tone': {'enum': list(GRID_TONES)},
                         'cells': {'type': 'array', 'items': {'type': 'array', 'items': S, 'maxItems': 3}}},
                         ['name', 'cells'])}},
                    ['periods', 'lanes']),
    # Price tiers side by side; the recommended one raised and dark.
    'tiers': _obj({'pick_label': S, 'items': {'type': 'array', 'minItems': 2, 'maxItems': 4, 'items': _obj({
                       'label': S, 'title': S, 'price': S, 'unit': S, 'meta': S, 'lines': LINES, 'billing': S,
                       'pick': {'type': 'boolean'}}, ['title', 'price'])}},
                  ['items']),
    # The questions a reader will ask, with our answers (appendix objections).
    'faq': _obj({'items': {'type': 'array', 'minItems': 2, 'maxItems': 6, 'items': _obj({'q': S, 'a': S}, ['q', 'a'])}},
                ['items']),
    # The math behind a price, set like a receipt.
    'ledger': _obj({'sections': {'type': 'array', 'minItems': 1, 'maxItems': 3, 'items': _obj({
                        'title': S, 'lines': {'type': 'array', 'minItems': 1, 'maxItems': 8, 'items': _obj({
                            'item': S, 'basis': S, 'amount': S}, ['item', 'amount'])},
                        'total': _obj({'label': S, 'amount': S}, ['label', 'amount'])}, ['title', 'lines'])}},
                   ['sections']),
    # A lifecycle ring: stages that go round again, the repeating thing in the middle.
    'ring': _obj({'center': _obj({'title': S, 'text': S}, ['title']),
                  'stages': {'type': 'array', 'minItems': 3, 'maxItems': 6, 'items': _obj({'title': S, 'text': S}, ['title'])}},
                 ['center', 'stages']),
    # A pause for the room: two to four questions, each with why we ask.
    'questions': _obj({'items': {'type': 'array', 'minItems': 2, 'maxItems': 4, 'items': _obj({
                           'q': S, 'why': S}, ['q'])},
                       'note': S}, ['items']),
    # One-line emphasis. At most one per slide (checked).
    'quote': _obj({'text': S, 'attribution': S}, ['text', 'attribution']),
    'takeaway': _obj({'lead': S, 'text': S}, ['lead']),
    'callout': _obj({'label': S, 'text': S, 'icon': S, 'tone': {'enum': ['green', 'amber']}}, ['label', 'text']),
    'band': _obj({'heading': S, 'lead': S, 'text': S}, ['heading']),
}
EMPHASIS = {'takeaway', 'callout', 'band', 'quote'}
EXCEPTIONS = {'table', 'diagram', 'image', 'hub', 'chart', 'gantt', 'flow', 'stack', 'swimlane',
              'adoption', 'approach', 'zoom', 'staircase', 'questions', 'middleout', 'processmap', 'board',
              'catalog', 'spectrum', 'options', 'matrix', 'cap', 'weekgrid', 'roadmap', 'tiers', 'faq', 'ledger', 'ring'}

COMPONENT = {'oneOf': [_obj({name: schema}, [name]) for name, schema in COMPONENTS.items()]}

COMMON = {'eyebrow': S, 'title': S, 'lede': S, 'source': S, 'notes': S}
SLIDES = {
    'cover': _obj({'eyebrow': S, 'title': S, 'subtitle': S, 'meta': S, 'notes': S}, ['title']),
    'section': _obj({'number': S, 'title': S, 'lede': S, 'notes': S}, ['title']),
    'content': _obj({**COMMON, 'body': {'type': 'array', 'items': COMPONENT, 'minItems': 1, 'maxItems': 3}},
                    ['title', 'body']),
    'bullets': _obj({**COMMON, 'points': _list(S, 2, 5)}, ['title', 'points']),
    'columns': _obj({**COMMON, 'left': _list(S, 1, 5), 'right': _list(S, 1, 5)}, ['title', 'left', 'right']),
    'comparison': _obj({**COMMON,
                        'left': _obj({'heading': S, 'points': _list(S, 1, 5)}, ['heading', 'points']),
                        'right': _obj({'heading': S, 'points': _list(S, 1, 5)}, ['heading', 'points'])},
                       ['title', 'left', 'right']),
    'numbers': _obj({**COMMON, 'stats': _list(_obj({'value': S, 'label': S}, ['value', 'label']), 3, 3)},
                    ['title', 'stats']),
    'quote': _obj({'text': S, 'attribution': S, 'notes': S}, ['text', 'attribution']),
    'picture': _obj({**COMMON, 'points': _list(S, 1, 4), 'image': S}, ['title', 'points', 'image']),
    # Five asks at most: a sixth pushed the button into the footer.
    'closing': _obj({'title': S, 'asks': _list(S, 2, 5), 'cta': S, 'notes': S}, ['title', 'asks']),
    # A full-bleed picture: a designed moment (a cold-open beat, a hero image). No title; the picture is the slide.
    'full': _obj({'image': S, 'alt': S, 'notes': S}, ['image', 'alt']),
    # Who we are: the title and how we work on the left, the people on a forest panel.
    'team': _obj({'eyebrow': S, 'title': S, 'notes': S, 'credentials': S, 'credentials_label': S,
                  'proof': _list(_obj({'lead': S, 'text': S}, ['lead', 'text']), 2, 4),
                  'stat': _obj({'value': S, 'label': S}, ['value', 'label']),
                  'logos': {'type': 'array', 'items': S, 'minItems': 2, 'maxItems': 6}, 'logos_label': S,
                  'points': _list(_obj({'icon': S, 'lead': S, 'text': S}, ['lead', 'text']), 2, 4),
                  'people': _list(_obj({'photo': S, 'name': S, 'role': S,
                                        'logos': {'type': 'array', 'items': S, 'maxItems': 3}},
                                       ['photo', 'name', 'role']), 1, 3)}, ['title', 'people']),
    # Full-bleed marketing slide: two photos cut corner to corner, one result each.
    'split': _obj({'tag': S, 'title': S, 'notes': S,
                   'left': _obj({'image': S, 'label': S, 'stat': S, 'headline': S, 'line': S},
                                ['image', 'label', 'stat', 'headline']),
                   'right': _obj({'image': S, 'label': S, 'stat': S, 'headline': S, 'line': S},
                                 ['image', 'label', 'stat', 'headline'])}, ['left', 'right']),
}
SLIDE = {'oneOf': [_obj({name: schema}, [name]) for name, schema in SLIDES.items()]}

SCHEMA = {
    'type': 'object',
    'properties': {
        'deck': S, 'client': S, 'date': S,
        # Whose brand the deck wears (brands/<id>/); default servantium. See brands.py.
        'brand': S,
        # Co-branding: the reader's logo beside ours on the cover ("Prepared for").
        'prepared_for': _obj({'name': S, 'logo': S}, ['name']),
        # Where `sv publish` files it: root customers (default) or demo, and a subfolder.
        'drive': _obj({'root': {'enum': ['customers', 'demo']}, 'folder': S}),
        'slides': {'type': 'array', 'items': SLIDE, 'minItems': 1},
    },
    'required': ['deck', 'client', 'slides'],
    'additionalProperties': False,
}


class _StrictLoader(yaml.SafeLoader):
    """Only strings, lists, maps, booleans and numbers. Dates stay strings."""


# Drop the timestamp resolver so `2026-09-29` stays a string.
_StrictLoader.yaml_implicit_resolvers = {
    k: [(tag, rx) for tag, rx in v if tag != 'tag:yaml.org,2002:timestamp']
    for k, v in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


class SpecError(Exception):
    pass


def _where(err):
    parts = []
    for p in err.absolute_path:
        parts.append(f'[{p + 1}]' if isinstance(p, int) and parts and parts[-1] == 'slides' else str(p))
    return '.'.join(parts) or '(top)'


def _numbers_to_text(data, rounds=50):
    """A number where the schema wants text (a stat value, a table cell, a year) becomes that
       text; numbers the schema wants as numbers (chart values, widths) stay numbers. Bound data
       arrives typed, so this is what lets a spec say value: "{{ co.headcount }}"."""
    v = Draft202012Validator(SCHEMA)
    for _ in range(rounds):
        fixed = 0
        for e in v.iter_errors(data):
            for err in [e, *(e.context or [])]:
                inst = err.instance
                if (err.validator == 'type' and isinstance(inst, (int, float)) and not isinstance(inst, bool)
                        and 'string' in (err.validator_value if isinstance(err.validator_value, list) else [err.validator_value])):
                    path = list(err.absolute_path)
                    node = data
                    for k in path[:-1]:
                        node = node[k]
                    if path:
                        node[path[-1]] = str(int(inst)) if float(inst).is_integer() else str(inst)
                        fixed += 1
        if not fixed:
            return data
    return data


def load(path):
    """Load and schema-validate a spec. Raises SpecError with readable messages."""
    path = Path(path)
    raw = path.read_text()
    try:
        data = yaml.load(raw, Loader=_StrictLoader)
    except yaml.YAMLError as e:
        raise SpecError(f'{path.name}: not valid YAML: {e}\n'
                        '  Most often: a value containing ": ", "?" or "#", or starting with a quote or '
                        'bracket. Put the value in double quotes.')
    if not isinstance(data, dict):
        raise SpecError(f'{path.name}: the spec must be a mapping with deck, client and slides')
    _numbers_to_text(data)
    errors = sorted(Draft202012Validator(SCHEMA).iter_errors(data), key=lambda e: list(e.absolute_path))
    if errors:
        msgs = []
        for e in errors[:12]:
            detail = e.message
            if e.validator == 'oneOf':
                detail = _explain_oneof(e)
            msgs.append(f'  {_where(e)}: {detail}')
        raise SpecError(f'{path.name} does not match the spec format:\n' + '\n'.join(msgs))
    data.setdefault('date', dt.date.today().isoformat())
    data['_path'] = str(path.resolve())
    data['_sha'] = hashlib.sha256(raw.encode()).hexdigest()[:12]
    return data


def _explain_oneof(err, prefix=''):
    """oneOf errors are unreadable by default. Find the type that was meant and report
       the deepest real problem inside it, recursing through nested oneOfs."""
    inst = err.instance
    if isinstance(inst, dict) and len(inst) == 1:
        (kind, value), = inst.items()
        pool = SLIDES if kind in SLIDES else COMPONENTS if kind in COMPONENTS else None
        if pool is None:
            options = ', '.join(sorted(SLIDES) + sorted(COMPONENTS))
            return f'{prefix}unknown type {kind!r}. Known types: {options}'
        stray = _comma_split(value)
        if stray:
            return (f'{prefix}{kind}: "{stray}" became a separate key. A comma inside {{...}} split a '
                    'value in two. Put the whole value in double quotes.')
        sub = sorted(Draft202012Validator(pool[kind]).iter_errors(value), key=lambda e: list(e.absolute_path))
        if sub:
            e = sub[0]
            where = '.'.join(str(p) for p in e.absolute_path)
            here = f'{prefix}{kind}{"." + where if where else ""}'
            if e.validator == 'oneOf':
                return _explain_oneof(e, here + ': ')
            msg = e.message
            if e.validator in ('minItems', 'maxItems') and kind in COMPONENTS:
                lo, hi = pool[kind].get('minItems', 2), pool[kind].get('maxItems', 4)
                msg += f' ({kind} takes {lo}-{hi} items: work in twos, threes and fours)'
            if e.validator == 'additionalProperties':
                msg += '. Check the field name against the spec format.'
            return f'{here}: {msg}'
    return prefix + err.message


def _comma_split(value):
    """YAML flow maps turn `text: a, b` into {'text': 'a', 'b': None}. Find that."""
    items = value if isinstance(value, list) else [value]
    for it in items:
        if isinstance(it, dict):
            for k, v in it.items():
                if v is None:
                    return k
    return None


def slides(spec):
    """Yield (number, kind, fields) for each slide."""
    for i, entry in enumerate(spec['slides'], 1):
        (kind, fields), = entry.items()
        yield i, kind, fields


def dump_schema(path):
    Path(path).write_text(json.dumps(SCHEMA, indent=1))
