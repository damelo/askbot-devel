import datetime
from django.db import models
from askbot.models.base import AnonymousContent
from askbot.models import content
from askbot import const

class AnswerManager(models.Manager):
    def create_new(
                self, 
                question=None, 
                author=None, 
                added_at=None, 
                wiki=False, 
                text='', 
                email_notify=False
            ):

        answer = Answer(
            question = question,
            author = author,
            added_at = added_at,
            wiki = wiki,
            text = text,
            #.html field is denormalized by the save() call
        )
        if answer.wiki:
            answer.last_edited_by = answer.author
            answer.last_edited_at = added_at
            answer.wikified_at = added_at

        answer.parse_and_save(author = author)

        answer.add_revision(
            author = author,
            revised_at = added_at,
            text = text,
            comment = const.POST_STATUS['default_version'],
        )

        #update question data
        question.thread.set_last_activity(last_activity_at=added_at, last_activity_by=author)

        question.thread.answer_count +=1
        question.thread.save()

        #set notification/delete
        if email_notify:
            question.thread.followed_by.add(author)
        else:
            question.thread.followed_by.remove(author)

        return answer

class Answer(content.Content):
    post_type = 'answer'
    question = models.ForeignKey('Question', related_name='answers')

    objects = AnswerManager()

    class Meta(content.Content.Meta):
        db_table = u'answer'


class AnonymousAnswer(AnonymousContent):
    question = models.ForeignKey('Question', related_name='anonymous_answers')

    def publish(self,user):
        added_at = datetime.datetime.now()
        Answer.objects.create_new(question=self.question,wiki=self.wiki,
                            added_at=added_at,text=self.text,
                            author=user)
        self.delete()
