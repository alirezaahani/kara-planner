## Project Overview

This project is a Flask web application that provides a personal dashboard for users to manage their schedules, goals, and exam results. The application uses Flask-SQLAlchemy for database interactions, Flask-Login for user management, and Flask-Minify to minify the responses.

## Database Models

The application uses four main models:

1. `User`: Represents a user with fields for id, username, email, password and name.
2. `Schedule`: Represents a user's schedule with fields for id, start time, end time, description, type and a foreign key to the User model.
3. `Goal`: Represents a user's goal with fields for id, deadline, description and a foreign key to the User model.
4. `ExamResult`: Represents a user's exam result with fields for id, date, type, value and a foreign key to the User model.

## Routes

The application provides several routes for managing the user's dashboard:

1. `/dashboard`: Displays the user's schedule for the current day, their goals for the week, and their exam results.
2. `/dashboard/edit`: Allows the user to edit their schedule for the current day.
3. `/dashboard/edit/add`: Allows the user to add a new schedule.
4. `/dashboard/edit/update`: Allows the user to update an existing schedule.
5. `/dashboard/edit/delete`: Allows a user to delete existing schedules
6. `/dashboard/goal`: Allows the user to view and edit their goals.
7. `/dashboard/update_add_goal`: Allows a user to update or add a new goal.
8. `/dashboard/delete_goal`: Allows a user to delete an existing goal.
9. `/dashboard/exam_results`: Displays the user's exam results.
10. `/dashboard/add_exam_result`: Allows the user to add a new exam result.
11. `/dashboard/delete_exam_result`: Allows the user to delete an existing exam result.

## Frontend

The frontend of the application is built using the Jinja2 templating engine. 

#### Main Page

- URL: `/dashboard`
- Overview: Provides a summary of the user's day, including their schedule and weekly goals.
- Components:
  - Schedule Timeline: The user's schedule is displayed using the vis.js library, visualizing events and time slots on a timeline.
  - Weekly Goals Table: A table displays the user's weekly goals, including goal ID, deadline, description, and corresponding actions.

#### Dashboard Page

- URL: `/dashboard/edit`
- Overview: Allows the user to add, edit, and delete schedules.
- Components:
  - Schedule Form: A form enables the user to add or edit schedules. The vis.js library is utilized to display the schedule on a timeline.
  - Double-Click Interaction: Double-clicking on the timeline enables users to add new schedules or modify existing ones.
  - Delete Button: Users can select a schedule and click the delete button to remove it. Changes are automatically saved to the server.

#### Exam Results Page

- URL: `/dashboard/exam_results`
- Overview: Enables users to add and view exam results, along with their progress over time.
- Components:
  - Exam Results List: Lists each exam result, including details such as the type, date, and value.
  - Delete Functionality: Users can delete exam results from the list.
  - Progress Visualization: The page utilizes Chart.js to plot a user's exam results on a graph, allowing them to visualize their progress over time.

#### Percentage Calculator Page

- URL: `/dashboard/percentage`
- Overview: Provides two types of calculators for percentage calculations.
- Components:
  - Simple Calculator: Takes inputs for correctly answered questions, incorrectly answered questions, and unanswered questions to calculate and display the total number of questions, the percentage considering negative marking, and the percentage without considering negative marking.
  - Advanced Calculator: Allows users to add multiple lessons, each with inputs for the lesson's coefficient, counts of correct, incorrect, and unanswered questions. Clicking a button calculates and displays the total percentage, the percentage without considering negative marking, and the total number of questions across all lessons.

#### Goal Page
- URL: `/dashboard/goal`
- Overview: Allows the user to view and edit their goals.
- Components:
   - A modal dialog defined with Bootstrap for adding/editing goals
   - Form with input fields for goal id, description, deadline date/time
   - Table to display list of existing goals
   - Buttons for completing, editing, and deleting goals
   - Imports Persian datetime picker library and initializes it for the deadline date/time field

## Running the Application

To run the application, you must have Flask installed. You can then run the application using the Flask command-line interface. The application uses SQLite as the database, so no additional database setup is required. The application also uses a secret key for session management, which is set to 'dev' in the application configuration.
