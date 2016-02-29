Feature: Sqlhistorian
  Background:
    Given I have an running volttron instance
    And I have running sqlhistorian instance
    And I have volttron 3.0 publish agent

  Scenario: Basic historian functionality. Publish to all topic and query from historian by topic name
    When I publish more than one point value to the all topic
    Then I should be able to get value of each point by querying by the specific topic name

  Scenario: Publish to all topic and query from historian based on topic name and exact timestamp
    When I publish value of the point, MixedAirTemperature, to the topic "devices/Building/LAB/Device/all" and <timestamp>
    Then I should be able to get value of the point by querying with topic="Building/LAB/Device/MixedAirTemperature" and with start as <timestamp>
    Examples:
    | timestamp |
    | datetime.utcnow().isoformat() |
    | datetime.utcnow().isoformat()+'Z' |
