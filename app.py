from email.message import Message
from botocore.exceptions import ClientError
import boto3
import email

workmail_message_flow = boto3.client('workmailmessageflow')
s3 = boto3.client('s3')


#Returns true or false if the email flag is found in the email.
def check_flag(parsed_msg)->bool:
    filter_header_value=parsed_msg.get('X-PERCEPTION-POINT-SPAM')
    if filter_header_value in ["FAIL","fail"]:
        return True
    return False

#This is the lambda handler function.
def lambda_handler(event, context):
 
    from_address = event['envelope']['mailFrom']['address']
    subject = event['subject']
    flow_direction = event['flowDirection']
    message_id = event['messageId']

    #Debugging information.
    print(f"Received email with message ID {message_id}, flowDirection {flow_direction}, from {from_address} with Subject {subject}")

    try:
        raw_msg = workmail_message_flow.get_raw_message_content(messageId=message_id)
        parsed_msg: Message = email.message_from_bytes(raw_msg['messageContent'].read())
        
        if(check_flag(parsed_msg)==True):
            return {
                'actions': [
                    {
                        'allRecipients': True,  # Rule is applied to all receipients
                        'action': {'type': 'MOVE_TO_JUNK'}  # Mail will be sent to the junk folder.
                    }
                ]
            }


    except ClientError as e:
        if e.response['Error']['Code'] == 'MessageFrozen':
            # Redirect emails are not eligible for update, handle it gracefully.
            print(f"Message {message_id} is not eligible for update. This is usually the case for a redirected email")
        else:
            # Send some context about this error to Lambda Logs
            print(e)
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                print(f"Message {message_id} does not exist. Messages in transit are no longer accessible after 1 day")
            elif e.response['Error']['Code'] == 'InvalidContentLocation':
                print('WorkMail could not access the updated email content.')
            raise(e)



