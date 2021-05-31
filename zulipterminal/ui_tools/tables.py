from typing import Any, List, Optional, Tuple, Union, cast


def parse_html_table(table_element: Any) -> Tuple[List[str], List[List[str]]]:
    """
    Parses an HTML table to extract cell items and column alignments.

    The table cells are stored in `cells` in a row-wise manner.
    cells = [[row0, row0, row0],
             [row1, row1, row1],
             [row2, row2, row2]]
    """
    headers = table_element.thead.tr.find_all("th")
    rows = table_element.tbody.find_all("tr")
    column_alignments = []

    # Add +1 to count the header row as well.
    cells: List[List[str]] = [[] for _ in range(len(rows) + 1)]

    # Fill up `cells` with the header/0th row and extract alignments.
    for header in headers:
        cells[0].append(header.text)
        column_alignments.append(header.get(("align"), "left"))

    # Fill up `cells` with body rows.
    for index, row in enumerate(rows, start=1):
        for tdata in row.find_all("td"):
            cells[index].append(tdata.text)
    return (column_alignments, cells)


StyledTableData = List[Union[str, Tuple[Optional[str], str]]]


def pad_row_strip(
    row_strip: StyledTableData, fill_char: str = " ", fill_width: int = 1
) -> StyledTableData:
    """
    Returns back a padded row strip.

    This only pads the box-drawing unicode characters. In particular, all the
    connector characters are padded both sides, the leftmost character is
    padded right and the rightmost is padded left.

    The structure of `row_strip` for a table with three columns:
    row_strip = [
        leftmost_char,
        cell_content,
        connector_char,
        cell_content,
        connector_char,
        cell_content,
        rightmost_char,
    ]

    Note: `cast` is used for assisting mypy.
    """
    fill = fill_char * fill_width

    # Pad the leftmost box-drawing character.
    row_strip[0] = cast(str, row_strip[0]) + fill

    # Pad the connector box-drawing characters.
    for index in range(2, len(row_strip) - 1, 2):
        row_strip[index] = fill + cast(str, row_strip[index]) + fill

    # Pad the rightmost box-drawing character.
    row_strip[-1] = fill + cast(str, row_strip[-1])
    return row_strip


def row_with_styled_content(
    row: List[str],
    column_alignments: List[str],
    column_widths: List[int],
    vertical_bar: str,
    row_style: Optional[str] = None,
) -> StyledTableData:
    """
    Constructs styled row strip, for markup table, using unicode characters
    and row elements.
    """
    aligner = {"center": str.center, "left": str.ljust, "right": str.rjust}
    row_strip: StyledTableData = [vertical_bar]
    for column_num, cell in enumerate(row):
        aligned_text = aligner[column_alignments[column_num]](
            cell, column_widths[column_num]
        )
        row_strip.extend([(row_style, aligned_text), vertical_bar])
    row_strip.pop()  # Remove the extra vertical_bar.
    row_strip.append(vertical_bar + "\n")
    return pad_row_strip(row_strip)


def row_with_only_border(
    lcorner: str,
    line: str,
    connector: str,
    rcorner: str,
    column_widths: List[int],
    newline: bool = True,
) -> StyledTableData:
    """
    Given left corner, line, connecter and right corner unicode character,
    constructs a border row strip for markup table.
    """
    border: StyledTableData = [lcorner]
    for width in column_widths:
        border.extend([line * width, connector])
    border.pop()  # Remove the extra connector.
    if newline:
        rcorner += "\n"
    border.append(rcorner)
    return pad_row_strip(border, fill_char=line)


def render_table(table_element: Any) -> StyledTableData:
    """
    A helper function for rendering a markup table in the MessageBox.
    """
    column_alignments, cells = parse_html_table(table_element)

    # Calculate the width required for each column.
    column_widths = [
        len(max(column, key=lambda string: len(string))) for column in zip(*cells)
    ]

    top_border = row_with_only_border("┌", "─", "┬", "┐", column_widths)
    middle_border = row_with_only_border("├", "─", "┼", "┤", column_widths)
    bottom_border = row_with_only_border(
        "└", "─", "┴", "┘", column_widths, newline=False
    )

    # Construct the table, row-by-row.
    table: StyledTableData = []

    # Add the header/0th row and the borders that surround it to the table.
    table.extend(top_border)
    table.extend(
        row_with_styled_content(
            cells.pop(0), column_alignments, column_widths, "│", row_style="table_head"
        )
    )
    table.extend(middle_border)

    # Add the body rows to the table followed by the bottom-most border in the
    # end.
    for row in cells:
        table.extend(
            row_with_styled_content(row, column_alignments, column_widths, "│")
        )
    table.extend(bottom_border)

    return table
