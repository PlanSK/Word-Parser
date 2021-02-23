SPACE_SYMBOL = ' '
SPACE_QUANTITY = 3
STR_LENGTH = 65
PARAGRAPH_INDENT = SPACE_SYMBOL * 4
INDENT = SPACE_SYMBOL * SPACE_QUANTITY
WORK_DIR = 'files/'
check_status = False
title = ''

replacing_dict = {'«': '"', '»': '"', '\t': INDENT}
from_str = 'From'
member_str = 'Member:'
where_str = 'Куда'
confident_str = 'Confidencial'
non_confident_str = 'For internal use'
non_confident_short_str = 'FIU'
abbreviations = {
    'department AWX': 'dAVX',
    'part': 'P',
    'administration': 'ADM'
}
director_str = 'Director'
number_abbr = 'NUM'
