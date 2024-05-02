from django.contrib.auth.models import Group, User
from rest_framework import permissions, viewsets
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from assistant.assistant_app.utils import handle_uploaded_file, create_random_uid
from assistant.assistant_app.gpt.open_api import client
from assistant.models import SessionMapping

from assistant.assistant_app.serializers import GroupSerializer, UserSerializer

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all().order_by('name')
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]


class HelloApiView(APIView):

    def get(self, request):
        return Response({"res": "hello world"}, status=status.HTTP_200_OK)


'''
    Keeping it simple: gets a session uid checks it agains sessions stored in the DB
    and bases on that returns the thread available for chat, also can add files to this
    chat thread
'''

class AskAnything(APIView):

    def post(self, request):
        try:
            session_uid = request.data.get('session_uid')
            question = request.data.get('question')
            if not session_uid or not question:
                return Response({"status": "Required Fields Missing"}, status=status.HTTP_400_BAD_REQUEST)

            if request.FILES.get('file'):
                file = request.FILES["file"]
                path = handle_uploaded_file(file, session_uid + "2")
                message_file = client.files.create(
                    file=open(path.name, "rb"), purpose="assistants"
                )
            else:
                message_file = None
            
            qs = SessionMapping.objects.filter(
                session_uid = session_uid,
            ).first()
            
            if not qs:
                return Response({"status": "No chat threads found"}, status=status.HTTP_400_BAD_REQUEST)
    
            thread_id = qs.thread_id
            assistant_id = qs.assistant_id

            if message_file:
                attachments = [
                    { "file_id": message_file.id, "tools": [{"type": "file_search"}] }
                ]
            else:
                attachments = []
            message = client.beta.threads.messages.create(
                thread_id = thread_id,
                role = "user",
                content = question,
                attachments = attachments
            )

            run = client.beta.threads.runs.create_and_poll(
                thread_id = thread_id, assistant_id = assistant_id
            )

            messages = list(client.beta.threads.messages.list(thread_id=thread_id, run_id=run.id))
            message_content = messages[0].content[0].text

            return Response({"response": message_content}, status=status.HTTP_200_OK)
        except Exception as e:
            print("e", e)
            return Response({"status": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


'''
    Just get a name for the bot, description, instructions and files for the vector store
    create a assistant a vector store associate both together and creates a thread for the 
    chat 
'''

class InitAssistant(APIView):

    def post(self, request):
        try:
            name = request.data.get('name')
            description = request.data.get('description')
            instructions = request.data.get('instructions')
            files = request.FILES.getlist('file')
            session_uid = create_random_uid()
            file_paths = []
            
            '''
                These files can be uploaded to S3 and then pick from there 
                currently storing it in uploaded_files folder

                Also number or files can be really large so we can break this api
                in two where we create a vector store separately and upload files in
                batches i.e 5 or 10 at a time from client
            '''
            for file in files:
                if file:
                    path = handle_uploaded_file(file, session_uid + "1")
                    file_paths.append(path.name)
            if not name or not description or not instructions:
                raise Exception()
            assistant = client.beta.assistants.create(
                name = name,
                description=description,
                instructions=instructions,
                model="gpt-4-turbo",
                tools = [{ "type": "file_search" }],
            )
            if file_paths and len(file_paths):
                vector_store = client.beta.vector_stores.create(name=session_uid)
                file_streams = [open(path, "rb") for path in file_paths]

                file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
                    vector_store_id = vector_store.id,
                    files = file_streams
                )
            
                assistant = client.beta.assistants.update(
                    assistant_id = assistant.id,
                    tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
                )

            thread = client.beta.threads.create()

            SessionMapping.objects.create(
                session_uid = session_uid,
                thread_id = thread.id,
                assistant_id = assistant.id
            )

            return Response({"Status": "Success", "session_uid": session_uid},status=status.HTTP_200_OK)
        except Exception as e:
            print("e", e)
            return Response({"status": "Something went wrong" + e}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
