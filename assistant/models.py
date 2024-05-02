from django.db import models

# Create your models here.
'''
    This should have a pre save hook here to validate uniqueness of session_uid or 
    else if not unique generate a new one until gets a unique. 
    
    We can have another table where we can store the configuration of vector_store.id to 
    files mapping and another table for assistant to vector_store.ids
'''
class SessionMapping(models.Model):
    session_uid = models.CharField(blank=False, db_index=True, null=False, max_length=16)
    thread_id = models.CharField(blank=False, null=False, max_length=160)
    assistant_id = models.CharField(blank=False, null=False, max_length=160)