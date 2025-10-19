Feature: Create a new course

As a Teacher
I want to create a course
So that students can enroll and complete challenges.

Background:
I am logged in as a Teacher
And I am on the "courses" page

Scenario: Create course successfully
When I click "Create Course"
Then the "Create Course" form appears
When I enter "Math Basics" as the title
And "Introduction to basic math principles" as the description
And select "English" as the language
And "Beginner" as the level
And press "Create"
Then I see the "Course Details" page
And a success message appears

Scenario: Fail to create a course with invalid data
When I leave title and description empty
And press "Create"
Then I stay on the create form
And an error message is shown
