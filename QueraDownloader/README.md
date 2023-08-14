# Quera HW Downloader
This scripts downloads all HW files of an assignment and unzips them in directories with student ids as their names.
## How to use
First you have to install the requirements and set the `QUERA_SESSION_ID` in `.env` file from `session_id` in your Quera cookies.
Now extract the assignment id from the URL in below pattern:

`https://quera.org/course/assignments/[HW_ID]/problems`

Finally you run the scripts with the arguments as follows:

`python dl.py [HW ID] [HW Dir]`