Feature: Edit an existing course

As a Teacher
I want to edit a course
So that I can update its information or correct mistakes.

Background:
I am logged in as a Teacher
And I am on the "course details" page

Scenario: Edit course successfully
When I click "Edit Course"
Then the "Edit Course" form appears
When I change the title to "Updated Math Basics"
And update the description
And press "Save"
Then I see the updated "Course Details" page
And a success message appears

Scenario: Fail to edit a course with invalid data
When I remove the title and press "Save"
Then I stay on the edit form
And an error message is shown
