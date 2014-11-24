Feature: Merge table cells
  In order to form a table cell spanning multiple rows and/or columns
  As a developer using python-docx
  I need a way to merge a range of cells

  @wip
  Scenario Outline: Merge cells
     Given a 3x3 table having only uniform cells
      When I merge from cell <origin> to cell <other>
      Then the row cells text is <expected-text>

    Examples: Reported row cell contents
      | origin | other | expected-text                             |
      |    1   |   2   | 1\2 1\2 3 4 5 6 7 8 9                     |
      |    2   |   5   | 1 2\5 3 4 2\5 6 7 8 9                     |
      |    5   |   9   | 1 2 3 4 5\6\8\9 5\6\8\9 7 5\6\8\9 5\6\8\9 |


  @wip
  Scenario Outline: Merge horizontal span with other cell
     Given a 3x3 table having a horizontal span
      When I merge from cell <origin> to cell <other>
      Then the row cells text is <expected-text>

    Examples: Reported row cell contents
      | origin | other | expected-text                     |
      |    4   |   8   | 1 2 3 4\7\8 4\7\8 6 4\7\8 4\7\8 9 |
      |    4   |   6   | 1 2 3 4\6 4\6 4\6 7 8 9           |
      |    2   |   4   | 1\2\4 1\2\4 3 1\2\4 1\2\4 6 7 8 9 |


  @wip
  Scenario Outline: Merge vertical span with other cell
     Given a 3x3 table having a vertical span
      When I merge from cell <origin> to cell <other>
      Then the row cells text is <expected-text>

    Examples: Reported row cell contents
      | origin | other | expected-text                     |
      |    5   |   9   | 1 2 3 4 5\6\9 5\6\9 7 5\6\9 5\6\9 |
      |    2   |   5   | 1 2\5 3 4 2\5 6 7 2\5 9           |
      |    7   |   5   | 1 2 3 4\5\7 4\5\7 6 4\5\7 4\5\7 9 |
