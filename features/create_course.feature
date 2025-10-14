Feature: Create a new course

  As a Teacher
  I want to create a course
  So that students can enroll and complete challenges.

  Background:
    Given I am logged in as an existing teacher with verified email

  Scenario: Successfully create a course
    When I send a POST request to "/api/platform/courses/create/" with the following data:
        |             |                                       |
        | title       | Math Basics                           |
        | description | Introduction to basic math principles |
        | language    | English                               |
        | level       | beginner                              |
        | status      | published                             |
    Then the course response status code should be 201
    And the course response should contain "Course created successfully."

  Scenario: Fail to create a course with missing title and description
    When I send a POST request to "/api/platform/courses/create/" with the following data:
      | title       |                                          |
      | description |                                          |
      | language    | English                                  |
      | level       | beginner                                 |
      | status      | draft                                    |
    Then the course response status code should be 400
    And the course response should contain "title"
