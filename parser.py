import sys
import re
import datetime

from loguru import logger
import docx

SPACE_SYMBOL = ' '
SPACE_QUANTITY = 3
STR_LENGTH = 65
PARAGRAPH_INDENT = 4
INDENT = SPACE_SYMBOL * SPACE_QUANTITY
check_status = False
title = ''


def read_file(file: str) -> list:
    try:
        doc = docx.Document(file)
        return [line.text for line in doc.paragraphs]
    except IOError:
        logger.critical(f"I can't open file {file}")
        return []


def file_lines_compile(file_line: list) -> list:
    resulting_list = []
    temp_list = []
    counter = 0
    first_block = False

    for line in file_line:
        replacing_dict = {'«': '"', '»': '"', '\t': INDENT}
        for char, replacing_char in replacing_dict.items():
            line = line.replace(char, replacing_char)
        line = line.strip()
        if line:
            if counter >= 2 and first_block:
                resulting_list.append(temp_list.copy())
                temp_list.clear()
            if 'From' in line[:3]:
                first_block = True
            temp_list.append(line)
            counter = 0
        else:
            counter += 1
    resulting_list.append(temp_list)

    while 'Director' not in resulting_list[-1][0][:10]:
        resulting_list[-2].extend(resulting_list[-1])
        resulting_list.pop()

    return resulting_list


def format_string(line: str, length=STR_LENGTH) -> str:
    if len(line.split()) < 2:
        return line

    new_str = line.split()
    while len(SPACE_SYMBOL.join(new_str)) < length:
        for index in range(len(new_str) - 1):
            if len(SPACE_SYMBOL.join(new_str)) < length:
                new_str[index] += SPACE_SYMBOL
            else:
                break
    return SPACE_SYMBOL.join(new_str)


def replacing_phrases(input_string: str) -> str:
    abbreviations = {
        'department AWX': 'dAVX',
        'part': 'P',
        'administration': 'ADM'
    }

    for key, value in abbreviations.items():
        if key in input_string:
            input_string = input_string.replace(key, value)
    return input_string


def header(header_list: list, number: int) -> list:
    # Defining urgency
    if re.search(r'^_+\s', header_list[2]):
        urgency = ''
    else:
        urgency = INDENT + re.search(r'\w+\s?\w+', header_list[2]).group(0)

    # Declassifying define
    declassify = re.split(r'\s{2,}', header_list[2])[1]
    list_item = ''
    if declassify == 'Confidencial':
        list_item = re.search(r'\(\w+\.\s?\d\.\d+(.*)\)$', header_list[3]).group(0)
        list_item = SPACE_SYMBOL * (STR_LENGTH - len(list_item)) + list_item
    elif declassify == 'For internal use':
        declassify = 'FIU'

    # compiling sender line information
    from_address, extended_address = header_list[5].split(',')

    from_address = re.sub(r'г\.\s', '', from_address)

    if from_address[-1] == 'ь':
        from_address = from_address[:-1] + 'и'
    elif from_address[-1] in 'лдргкв':
        from_address = from_address[:-1] + 'а'
    elif from_address[-1] in 'а':
        from_address = from_address[:-1] + 'ы'

    extended_address = replacing_phrases(extended_address)

    dot_symbol = ''
    from_address += extended_address
    number_of_part = from_address[-4:]
    if check_status:
        dot_symbol = '.'
    header_string = f'{from_address}{INDENT}NUM{dot_symbol}{SPACE_SYMBOL}{number}{INDENT}{declassify}{urgency}'

    return [header_string, list_item, number_of_part]


def address_where(recipient: list) -> list:
    address_list = list()
    quantity_spaces = 0

    if 'Куда' in recipient[0]:
        recipient[0] = recipient[0][11:].strip()
    if not recipient[0]:
        recipient.pop(0)

    if check_status:
        pair_address = [
            [recipient[i], recipient[i + 1]]
            for i in range(0, len(recipient), 2)
        ]
        for pair in pair_address:
            city = pair[0].split()[1] + INDENT
            where = replacing_phrases(pair[1])
            surplus = ''
            if len(city + where) > STR_LENGTH:
                surplus = where.split().pop()
                where = SPACE_SYMBOL.join(where.split()[:-1])
                surplus = 1 * len(city) + surplus

            address_list.append(city + where)
            if surplus:
                address_list.append(surplus)
    else:
        for string in recipient:
            if 'г.' in string[:3] and ',' in string:
                addressee_string = [
                    element.strip()
                    for element in string[3:].split(',')
                ]
                from_string = addressee_string[0]
                quantity_spaces = len(from_string) + 3
                address_list.append(f'{from_string}{INDENT}{addressee_string[1]}')
            elif 'г.' in string[:3] and re.search(r'\w{2,}\.', string):
                addressee_string = [element.strip() for element in string[3:].split('. ')]
                from_string = addressee_string[0]
                quantity_spaces = len(from_string) + 3
                address_list.append(f'{from_string}{INDENT}{addressee_string[1]}')
            elif len(re.split(r'\s{3,}', string)) > 1:
                for tab_string in re.split(r'\s{3,}', string):
                    address_list.append(f'{1 * quantity_spaces}{tab_string}')
            else:
                address_list.append(f'{1 * quantity_spaces}{string}')

    return address_list


def main_text(file_part: list) -> list:
    str_list = list()

    for paragraph in file_part:
        words_list = paragraph.split()
        start = 0

        for position, _ in enumerate(words_list):
            line = SPACE_SYMBOL.join(words_list[start:position])
            short_line = SPACE_SYMBOL.join(words_list[start:position - 1])
            end_line = SPACE_SYMBOL.join(words_list[start:])

            if start == 0 and len(line) > STR_LENGTH - 4:
                str_list.append(
                    PARAGRAPH_INDENT + format_string(short_line, length=STR_LENGTH - 4)
                )
                start = position - 1
            elif len(line) > STR_LENGTH:
                str_list.append(format_string(short_line))
                start = position - 1
            elif position == len(words_list) - 1 and len(end_line) <= STR_LENGTH:
                str_list.append(end_line)
            elif position == len(words_list) - 1 and len(end_line) > STR_LENGTH:
                str_list.append(format_string(line))
                str_list.append(words_list[-1])

    return str_list


def footer(file_line: list, number: int, number_of_part: str) -> list:
    final_result = list()
    check_symbol = ''
    today = datetime.date.today().strftime("%d.%m.%Y")
    if check_status:
        check_symbol = '/P'
    prefix = f'NUM {number_of_part}/{number}{check_symbol}{INDENT}'
    final_result.append(f'{prefix}{file_line[0]}')
    final_result.append(f'{SPACE_SYMBOL * len(prefix)}{file_line[1]}')
    rank, name, sub_name = file_line[2].split()
    left_part = f'{today}{SPACE_SYMBOL * (len(prefix) - len(today))}{rank}'
    names = name + SPACE_SYMBOL + sub_name
    space_string = SPACE_SYMBOL * (len(prefix + file_line[0]) - len(left_part + names))
    final_result.append(f'{left_part}{space_string}{names}')

    return final_result


def assignee(file_line: list) -> str:
    for s in file_line:
        if 'Member:' in s:
            return s


if __name__ == "__main__":
    # Default values
    file_name = ''
    message_number = 0
    check_status = False

    if len(sys.argv) == 4:
        file_name = sys.argv[1]
        message_number = sys.argv[2]
        check_status = True
        print(len(sys.argv))
    elif len(sys.argv) == 3:
        file_name = sys.argv[1]
        message_number = sys.argv[2]
    else:
        logger.error('Too few arguments.')
        exit()

    logger.info(f'Use {file_name} file. Number is {message_number}.')
    logger.info(f'Check ststus is {check_status}')

    file_parts = file_lines_compile(read_file(file_name))

    if not file_parts:
        exit()

    if not check_status:
        title = file_parts[2]

    header_result = header(file_parts[0], message_number)

    with open(f'files/{message_number}.atl', 'w', encoding='cp866') as out_file:
        print(*header_result[:2], sep='\n', file=out_file)
        print('\n', file=out_file)
        print(*address_where(file_parts[1]), sep='\n', file=out_file)
        print('\n', file=out_file)
        if title:
            print(*title, sep='\n', file=out_file)
        print('\n', file=out_file)
        print(*main_text(file_parts[-2]), sep='\n', file=out_file)
        print('\n', file=out_file)
        print(*footer(file_parts[-1], message_number, header_result[-1]), sep='\n', file=out_file)
        print('\n', file=out_file)
        print(assignee(file_parts[-1]), file=out_file)
