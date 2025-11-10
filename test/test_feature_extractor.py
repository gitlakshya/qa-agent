import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_pipeline.feature_extractor import FeatureExtractor
import logging
from llm.connector import azurellm
def test_featureExtraction(user_story, filePath, azurellm):
    feature = FeatureExtractor()
    result = feature.extract_features(user_story, filePath, azurellm)
    return result



if __name__ == "__main__":

    userStory = """As a developer, I want to migrate to the new email processing service version 2.0 , so that I can benefit from improved reliability, functionality  and reduced maintenance overhead.

Acceptance Criteria 

Create request via email should work as is 

along with attachment 

all the validation scenarios should work as is 

Failure scenarios should be checked 

New Failure scenarios needs to be handled 

Create comment via email should work as is

along with attachment 

all the validation scenarios should work as is 

Failure scenarios should be checked 

New Failure scenarios needs to be handled 

https://elevateservices.atlassian.net/wiki/spaces/CORE/pages/2221539386/Email+Processing+Service+v2 



Migration to new email service allows MR to address scenarios which previously couldn’t be supported/weren’t feasible

Only the new cases have to addressed, existing cases are added only for reference.



Category

New email (body)

Receiver

New case

User profile (metadata)

Request creation failed as ‘your profile doesn’t not have the relevant metadata (BU, Geo, Req type) assigned to to create request via email.’

Please contact your admin to update your user profile.

Request creator & tenant admin

N

User profile (metadata)

Request creation failed as ‘your profile doesn’t not have the relevant metadata (BU, Geo, Req type) assigned to to create request via email.’ Please contact your admin to update your user profile.

Request creator & tenant admin

N

Request type not created

Request creation failed as this feature has not been enabled. Please contact your admin to enable it.

Request creator & tenant admin

N

Attachment (File size, type, # of files in a request, duplicate files names)

Request creation failed as ‘the total limit of attached files exceeds 25MB.’ Please try to create requests with a smaller file size to submit the request.

Request creator & tenant admin

N

Attachment (File size, type, # of files in a request, duplicate files names)

Request creation failed as it contains files with duplicate names. Please add files with unique names.

Request creator & tenant admin

N

Attachment (File size, type, # of files in a request, duplicate files names)

Request creation failed as the no of attachments exceed the total limit of 15. Please create request with fewer files.

Request creator & tenant admin

N

Attachment (File size, type, # of files in a request, duplicate files names)

No change

Request creator & tenant admin

N

Special characters

Request creation failed as the email has been blocked by firewall to protect against vulnerabilities by filtering out potentially malicious traffic.

Request creator & tenant admin

N

Firewall

Same as above

Request creator & tenant admin

N

User not registered

No change

Request creator & tenant admin

N

[Comment] Reply to comment failure when users responds on ‘Do not reply email’

Your email couldn’t be this email doesn’t process replies.

To ensure it is sucessfully created, please create it directly in ELM's  interface. 





User who replied to notification

Y

[System error] Email couldn't be parsed

Your email could not be processed due to a system error. To ensure it is sucessfully created, please create it directly in ELM's  interface. 

""

Y

[System error] Email classification model when invoked gives error

""

""

Y

[System error] Email fails to process & system moves to an exception state

""

""

Y

[System error] Documents failed to process due to API failure  or couldn't be processed

Your email was created successfully, but one or more attachments could not be added.  Please upload the missing file(s) using ELM's interface

""

Y

Email template


Case

Subject

Title

Description

[Comment] Reply to comment failure when users responds on ‘Do not reply email’

[Same thread]

Comment failed

Hi [Users' name],



[System error] Email couldn't be parsed

[Type] could not be processed

[Type]is Request or Comment

[Type] could not be processed

Hi [Users' name],

Your email could not be processed due to a system error. To ensure it is sucessful, please create it directly using ELM's interface. 

[System error] Email classification model when invoked gives error

““

““

""

[System error] Email fails to process & system moves to an exception state

““

““

""

[System error] Documents failed to process due to API failure  or couldn't be processed

Action needed: [Type] partially created

Action needed: [Type] partially created

Hi [Users' name] 

Your email was created successfully, but one or more attachments could not be added.  Please upload the missing file(s) using ELM's interface

"""

    filePath = r'Related_docs\Requests_Module_Documentation_v13.0.0.0.pdf'

    try:
        result = test_featureExtraction(userStory, filePath, azurellm)
        print("Feature Extraction Result:", result)
    except Exception as e:
        logging.error(f"Error during feature extraction: {e}")