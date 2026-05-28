# Project Report

#### The Team members

* Names, epita email addresses, and GitHub usernames of all team members.
Yara Nehme: yara.nehme@epita.fr, ynehme-coder
Fatemeh Ahmadpour, fatemeh.ahmadpour@epita.fr, Fate-amp
Ashneel Girivar Bhagoban, ashneel-girivar.bhagoban@epita.fr, Ashh7121
---

#### Initial Design

* initial architecture
* assumptions
* technical choices
Initially, we knew how to implement google genai using the API key and chromadb based on what we learned in lab14 and 15. But what we hadn't thought of was the document processing and the input AI receives and then outputs. For example how pdf files, images, OCR characters were going to be processed.
For the frontend and the backend, we decided for falsk because we didn't need to do any API glueing, which we thought would help the speed of the application.

So the **initial techincal choices** were: Flask, SQLite(to keep the db light, we did consider using cloud, but we overules that), google.genai library and chromaDB

**Further technical choices:**

1. For document processing, we added pdfplumber to extract text from pdf files as ai cannot receive pdf files as the context.
2.  To handle OCR character and DOCX documents, we later added pytesseract and python-docx
3. PIL to handle images
4. SQLAlchemy to be to talk to the database in python, preventing sql queries breaking the application
5. python-dotenv to be able to load our API key from .env, since env is not automatically loaded in python files
---

#### Engineering Decisions

For each major decision:

* what alternatives were considered?

1. For the db, we first considered uploading a mysql database on the cloud or on one of our machines, but that had the 
2. We considered using next.js as our fullstack application instead of flask, but next.js is an incredibly heavy framework and our team members were not comfortable with JS

* why was this solution chosen?
Since speed was an important factor as the app should stream answers fast enough, we decided to go with flask and SQLite rather than heavier alternatives like next.js and mysql. 
---

#### Who Did What?

* Document how the project was originally divided among each team member.
We did eventually touch the other parts as well as we started to glue everything together but these were the main initial roles:

Yara: Frontend
Maya: AI agent and embeddings
Ashneel: Backend
* Document how responsibilities possibly evolved over time.
At first, we worked on creating the architecture and the skeleton together. We had to come up with a prompt as a group to get a working skeleton with clear TODOs for each person. Each person did work on the indicated parts, but eventually at the end of the project, we started working on the other parts as well, as we had to make the whole application working rather than different parts separately.
---

#### AI Collaboration

Document how AI tools were used.

* What tools were used for what purposes?

1. Claude Haiku 4.5 agent mode was used to create a skeleton for the project
2. We used AI to divide the three main parts of the project and define clear objectives for each person invloved
3. We did use AI to code, but it was a mixture of coding and asking about the code so that we would be able to pinpoints bugs later on
4. We also used the agent mode for pinpointing bugs, as sometimes the errors were very vague, like the 500 server error that we were getting intially while trying to generate a reponse(we knew from tests in the code that the agent was initialized and works fine)

* How did AI influence design and implementation decisions?
Something that we didn't know at the beginning of the project was to tell AI to go easy with the skeleton. We put verything that we understood from the requirements and told AI about our time constraint of 10 days and it created a heavy structure for a limited project. We should have clarified how we wanted our output to look like and how heavy we want it to be because AI aims for perfection when you do not clarify

* How did AI impact your learning and development process?
As the skeleton was rather heavy and huge, it was sometimes difficult to pinpoint problems and know what the life cycle of the app looks like. We used AI specifically in this part, to help us learn about the life cycle of the application and explain in clear terms what each part is supposed to achieve, which was very critical in the development of the app.

* How did you evaluate AI-generated suggestions?
First of all, the initial suggestion was a bit too ambitious for our time window. Secondly, I think we had more hallucinations when the app grew bigger.

* How did you detect and handle AI errors or limitations?
We detected the errors when the suggested solutions were deprecated or when AI was being very vague in the answers, making changes that had obviously nothing to do with our problem. Lastly, by simply running our application and seeing the result(which was not idea, like the 500 error, because frontend errors are usually really vague)
Mostly by improving our pompts and provide more context of where we thought the bugs were coming from.
---

#### Failures and Iterations

Document:

* what failed?
* what surprised you?
* what required redesign?

---

#### “When AI Failed or Was Wrong”

Document cases where AI-generated advice, code, or explanations were:

* incomplete
* misleading
* incorrect
* inefficient

Explain how you detected the issue and how you resolved it.

---

#### Lessons Learned

Reflect on:

* technical growth
* workflow improvements
* Strengths and limitations of AI-assisted development

