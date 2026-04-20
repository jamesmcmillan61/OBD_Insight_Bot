# OBD Inisght bot - handover document

## Project Structure. 

The project is in a folder called 2526 – IBM OBD Insight Bot. This is then split into three folders named: AI, WebApp, and Docs. The AI folder contains the python code for the AI side of the project. The WebApp folder contains all code for the project's front end. Finally in Docs you will find the technical documentation for the project within depth description of how the code works. There are also two YAML files, one named azure-pipelines-api-windows.yml and the other named azure-pipelines-webapp-iis.yml. These files are for a CI/CD pipeline that will automatically update the main website when run by an agent. 

## deployment 
How to deploy this application can be found [here](HowTodeploy.md)

## How do you use the product? 

First type in the link of the website. On the home page you will see a blue button that says start your free analysis press that. A TOS will pop up please read and then press continue. The next page is where the application is you get two options either upload your own OBD csv file or input your car data manually. If your file does not have the same table titles as the example file in the repo, please input your data manually. Once you have inputted the data you will see a bar at the bottom you can type in any questions relating to your cars health otherwise there are little buttons you can press which give you example questions. Once you press a button or answer a question, wait and the AI will respond with an answer.   

## Known issues. 

A lack of resources within the VM meant that the trained model could not be that intelligent as we physically would not have been able to given the resource restraints. This means that the model could give wrong answers or might respond incorrectly at certain times, but this is covered by several notices throughout the web page. 

 

The project pipeline does not automatically include the AI model side, and this must be done manually. 

 

 

## Where you could develop next. 

Increasing the resources on the VM would allow for scalability and an improvement in the model. This would allow us to refine the model and allow for a larger scale deployment for users to access. Within the limitations of the VM and the project we could only deploy the webapp and model within the campus network thus making it inaccessible from outside of the campus. 

 

Adding more items to the dictionary used by the model would improve the webapp as the model would be able to talk about more fault codes and fault scenarios to aid the user further. These expansions were omitted from the project as the amount of memory the model could have was not large enough to cover a greater proportion of the fault codes. 

 

There are no alternate language options which would help the webapp to be used within multiple countries rather than an English-speaking audience. This was outside of the scope of our project but could be something to develop in the future. Common languages like French, Chinese or Spanish would be the highest priority languages as they would expand the countries that could use the webapp.