Feature: Update an existing course
  As a Teacher
  I want to edit a course
  So that I can change its title or details after creation.

  Background:
    Given I am logged in as an existing teacher with verified email for updating
    And a course already exists with title "Math Basics" and slug "math-basics"

  Scenario: Successfully update a course
    When I send a PATCH request to "/api/platform/courses/{course_slug}/update/" with the following data:
      |             |                              |
      | title       | Advanced Math Basics 2       |
      | description | Updated course description   |
      | level       | intermediate                 |
      | status      | published                    |
    Then the course update response status code should be 200
    And the course response should contain "Advanced Math Basics"

  Scenario: Fail to update course with invalid data
    When I send a PATCH request to "/api/platform/courses/{course_slug}/update/" with the following data:
      |             |                              |
      | title       |                              |
      | description |                              |
    Then the course update response should contain "No changes detected"
    And the course response should contain "title"
