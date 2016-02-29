Feature: test feature
  Scenario Outline: Outlined given, when, thens
    Given there are <start> cucumbers
    When I eat <eat> cucumbers
    Then I should have <eat> <left> cucumbers
      and no more

    Examples:
    | start | eat | left |
    | 12    | 2   | 10 |
    | 10    | 3   | 7 |