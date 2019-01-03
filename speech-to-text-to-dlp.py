#!/usr/bin/python

import io
import os
import re

# Imports the Google Cloud client library
from google.cloud import speech
from google.cloud import dlp
from google.cloud.speech import enums
from google.cloud.speech import types

# Instantiates a client
speechClient = speech.SpeechClient()

dlpClient = dlp.DlpServiceClient()

parent = dlpClient.project_path('speech-samples-galvink')

# Prepare info_types by converting the list of strings into a list of
info_types = ['PHONE_NUMBER', 'EMAIL_ADDRESS', 'CREDIT_CARD_NUMBER', 'US_SOCIAL_SECURITY_NUMBER']
# dictionaries (protos are also accepted).
inspect_config = {
    'info_types': [{'name': info_type} for info_type in info_types]
}
# Construct deidentify configuration dictionary
deidentify_config = {
    'info_type_transformations': {
        'transformations': [
            {
                'primitive_transformation': {
                    'replace_with_info_type_config': {

                    }
                }
            }
        ]
    }
}

# The name of the audio file to transcribe
file_name = os.path.join(
    os.path.dirname(__file__),
    'resources',
    'sallybrown.flac')

# Loads the audio into memory
with io.open(file_name, 'rb') as audio_file:
    content = audio_file.read()
    audio = types.RecognitionAudio(content=content)

config = types.RecognitionConfig(
    encoding=enums.RecognitionConfig.AudioEncoding.FLAC,
    sample_rate_hertz=16000,
    language_code='en-US')

# Detects speech in the audio file
response = speechClient.recognize(config, audio)

transcript = ""

for result in response.results:
    transcript = transcript + result.alternatives[0].transcript;

print('Original Transcript: {}'.format(transcript))

# Check transcription for email address, since speech-to-text returns " at " instead of "@"
# Format with regex before sending to DLP api
# Currently social security numbers and credit card numbers are interpreted as phone numbers

regex = r".([A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+)*)(\sat\s+)((?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9]))"

updatedTranscript = re.sub(regex, r" \1@\3", transcript)

print('Email addresses reformatted: {}'.format(updatedTranscript))

# Construct item
item = {'value': updatedTranscript}

# Call the API
dlpResponse = dlpClient.deidentify_content(
    parent, inspect_config=inspect_config,
    deidentify_config=deidentify_config, item=item)

# Print out the results.
print('Final Result with sensitive content redacted: {}'.format(dlpResponse.item.value))
# [END dlp_deidentify_masking]
