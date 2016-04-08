from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,logout,login
import datetime
from django.utils.datastructures import MultiValueDictKeyError
from django.core.paginator import Paginator,EmptyPage,InvalidPage

from .forms import CodehubTopicForm,CodehubTopicCommentForm,SearchForm,CodehubQuestionForm,CodehubQuestionCommentForm
from .models import CodehubTopicModel,CodehubTopicCommentModel,CodehubQuestionModel,CodehubQuestionCommentModel
from .views import loginRequired

from taggit.models import Tag


#decorator for checking that only the user of the topic can comment
def check_user_access_for_topic_edit(func):
    def wrapper(request,id,*args,**kwargs):
        # topic_details = CodehubTopicModel.objects.get(id = id)
        topic_details = get_object_or_404(CodehubTopicModel,id =id)
        if topic_details.user.username != request.user.username:
            return redirect('/codehub/topic')
        return func(request,id,*args,**kwargs)
    return wrapper


#does the pagination stuff here
def do_pagination(request,list,num_of_pages):
    paginator = Paginator(list,num_of_pages)
    try:
        page = int(request.GET.get('page','1'))
    except:
        page = 1

    try:
        data = paginator.page(page)
    except(EmptyPage,InvalidPage):
        data = paginator.page(paginator.num_pages)

    return data


@loginRequired
def codehub(request):
    form = CodehubTopicForm()
    return render(request,'codehub/index.html',{'form':form})


@loginRequired
def codehub_topic(request):
    if request.method == 'POST':
        form = CodehubTopicForm(request.POST)
        if form.is_valid():
            user = User.objects.get(username = request.user.username)
            tags = form.cleaned_data['tags']
            try:
                file = request.FILES['file']
            except MultiValueDictKeyError:
                file = ''
            new_topic = CodehubTopicModel(
                user = user,
                topic_heading = form.cleaned_data['topic_heading'],
                topic_detail = form.cleaned_data['topic_detail'],
                topic_link = form.cleaned_data['topic_link'],
                topic_type = form.cleaned_data['topic_type'],
                file = file,
                timeStamp = datetime.datetime.now(),
            )
            new_topic.save()
            new_topic.tags.add(*tags)
            #add flash message
            return redirect('/codehub/topic')
    else:
        form = CodehubTopicForm()
    search_form = SearchForm()
    topics_list = CodehubTopicModel.objects.all().order_by('-timeStamp')
    topics = do_pagination(request,topics_list,3)  #it does the pagination stuff
    return render(request,'codehub/topic/topic.html',{'form':form,'topics':topics,'search_form':search_form})




@loginRequired
@check_user_access_for_topic_edit
def edit_topic(request,id):
    if request.method == 'POST':
        form = CodehubTopicForm(request.POST)
        if form.is_valid():
            initial_topic_details = CodehubTopicModel.objects.get(id=id)
            try:
                initial_topic_details.file = request.FILES['file']
            except:
                initial_topic_details.file = ''
            form = CodehubTopicForm(request.POST,instance = initial_topic_details)
            form.save()
            #flash message for edit data
            print 'data edited'
            return redirect('/codehub/topic')
    else:
        topic_details = CodehubTopicModel.objects.get(id = id)
        tagArr = []
        for tag in topic_details.tags.all():
            tagArr.append(tag.name)
        tags = ",".join(tagArr)
        data = {'topic_heading':topic_details.topic_heading,'topic_detail':topic_details.topic_detail,'topic_link':topic_details.topic_link,'file':topic_details.file,'topic_type':topic_details.topic_type,'tags':tags}
        form = CodehubTopicForm(initial = data)
    return render(request,'codehub/topic/edit_topic.html',{'form':form})



#check that only the user can delete or removw his posts only
@loginRequired
@check_user_access_for_topic_edit
def remove_topic(request,id):
    get_object_or_404(CodehubTopicModel,id = id).delete()
    print 'deleted'
    return redirect('/codehub/topic')



@loginRequired
def comment_on_topic(request,id):
    if request.method == 'POST':
        form = CodehubTopicCommentForm(request.POST)
        if form.is_valid():
            new_comment = CodehubTopicCommentModel(
                user = User.objects.get(username = request.user.username),
                topic = CodehubTopicModel.objects.get(id = id),
                comment_text = form.cleaned_data['comment_text'],
                timeStamp = datetime.datetime.now()
            )
            new_comment.save()
            #flash message here
            return redirect("/codehub/topic/"+id+"/comment")
    else:
        form = CodehubTopicCommentForm()
    comments = CodehubTopicCommentModel.objects.filter(topic_id = id).order_by('-timeStamp')
    topic_details = CodehubTopicModel.objects.get(id = id)
    return render(request,'codehub/topic/comment_on_topic.html',{'form':form,'comments':comments,'topic':topic_details})



@loginRequired
def search_topic(request):
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            string = request.POST['search_str']
            print string
            result = CodehubTopicModel.objects.filter(topic_heading__contains=string)
            return HttpResponse(result)
    else:
        form = SearchForm()
    return HttpResponse('cdbckdbckj')



#COMMENT ROUTES START here
def check_user_access_for_comment_edit(func):
    def wrapper(request,id,*args,**kwargs):
        # comment_details = CodehubTopicCommentModel.objects.get(id = id)
        comment_details = get_object_or_404(CodehubTopicCommentModel,id = id)
        if comment_details.user.username != request.user.username:
            return redirect('/codehub/topic')
        return func(request,id,*args,**kwargs)
    return wrapper



@loginRequired
@check_user_access_for_comment_edit
def remove_topic_comment(request,id):
    #get the id of the topic of the comment
    # topic_id = CodehubTopicCommentModel.objects.get(id = id).topic.id
    topic_id = get_object_or_404(CodehubTopicCommentModel,id =id).topic.id
    get_object_or_404(CodehubTopicCommentModel,id = id).delete()
    return redirect('/codehub/topic/'+str(topic_id)+'/comment')



@loginRequired
@check_user_access_for_comment_edit
def edit_topic_comment(request,id):
    if request.method == 'POST':
        form = CodehubTopicCommentForm(request.POST)
        if form.is_valid():
            comment = CodehubTopicCommentModel.objects.get(id = id)
            form = CodehubTopicCommentForm(request.POST,instance = comment)
            form.save()
            return redirect('/codehub/topic/'+str(comment.topic.id)+'/comment')
    else:
        comment = CodehubTopicCommentModel.objects.get(id = id)
        comment_data = {'comment_text':comment.comment_text}
        form = CodehubTopicCommentForm(initial = comment_data)
    return render(request,'codehub/topic/edit_comment_on_topic.html',{'form':form})



#question section starts here

#decorators for login section comes here
def check_user_access_for_question_edit_or_remove(func):
    def wrapper(request,ques_id,*args,**kwargs):
        ques_details = get_object_or_404(CodehubQuestionModel,id = ques_id)
        if ques_details.user.username != request.user.username:
            return redirect('/codehub')
        return func(request,ques_id,*args,**kwargs)
    return wrapper


@loginRequired
def codehub_question(request):
    if request.method == 'POST':
        form = CodehubQuestionForm(request.POST)
        if form.is_valid():
            tags = form.cleaned_data['question_tags']
            new_ques = CodehubQuestionModel(
                user = request.user,
                question_heading = form.cleaned_data['question_heading'],
                question_description = form.cleaned_data['question_description'],
                question_link = form.cleaned_data['question_link'],
                question_type = form.cleaned_data['question_type']
            )
            new_ques.save()
            new_ques.question_tags.add(*tags)
            return redirect('/codehub/question')
    else:
        form = CodehubQuestionForm()
    codehub_questions_list = CodehubQuestionModel.objects.all().order_by("-timeStamp")
    codehub_questions = do_pagination(request,codehub_questions_list,2)
    return render(request,'codehub/question/question.html',{'form':form,'questions':codehub_questions})



@loginRequired
def codehub_question_details(request,ques_id):
    if request.method == 'POST':
        form = CodehubQuestionCommentForm(request.POST)
        if form.is_valid():
            new_answer = CodehubQuestionCommentModel(
                user = request.user,
                question = get_object_or_404(CodehubQuestionModel,id = ques_id),
                comment_text = form.cleaned_data['comment_text']
            )
            new_answer.save()
            print 'saved'
    else:
        form = CodehubQuestionCommentForm()
    ques_details = get_object_or_404(CodehubQuestionModel,id = ques_id)
    ques_answers = CodehubQuestionCommentModel.objects.filter(question_id = ques_id).order_by("-timeStamp")
    return render(request,'codehub/question/question_details.html',{'ques_details':ques_details,'form':form,'ques_answers':ques_answers})


@loginRequired
@check_user_access_for_question_edit_or_remove
def remove_codehub_question(request,ques_id):
    ques_details = get_object_or_404(CodehubQuestionModel,id = ques_id)
    ques_user_id = ques_details.user.id
    ques_details.delete()
    print 'deleted'
    return redirect('/user/'+str(ques_user_id)+'/questions/')
    #flash message here

@loginRequired
@check_user_access_for_question_edit_or_remove
def edit_codehub_question(request,ques_id):
    if request.method == 'POST':
        form = CodehubQuestionForm(request.POST)
        if form.is_valid():
            ques_details = get_object_or_404(CodehubQuestionModel,id = ques_id)
            form = CodehubQuestionForm(request.POST,instance = ques_details)
            form.save()
            # flash messge here
            return redirect('/codehub/question/' +str(ques_id) + '/details/')
    else:
        ques_details = get_object_or_404(CodehubQuestionModel,id = ques_id)
        tagArr = []
        for tag in ques_details.question_tags.all():
            tagArr.append(tag.name)
        tags = ",".join(tagArr)
        ques_data = {'question_heading':ques_details.question_heading,'question_description':ques_details.question_description,'question_link':ques_details.question_link,'question_type':ques_details.question_type,'question_tags':tags}
        form = CodehubQuestionForm(initial = ques_data)
    return render(request,'codehub/question/edit_question.html',{'form':form})


@loginRequired
def remove_codehub_question_comment(request,ans_id):
    c_details = get_object_or_404(CodehubQuestionCommentModel,id = ans_id)
    ques_id = c_details.question.id
    c_details.delete()
    return redirect('/codehub/question/'+str(ques_id)+'/details/')


def edit_codehub_question_comment(request,ans_id):
    if request.method == 'POST':
        form = CodehubQuestionCommentForm(request.POST)
        if form.is_valid():
            ans_details = get_object_or_404(CodehubQuestionCommentModel,id = ans_id)
            ques_id = ans_details.question.id
            form = CodehubQuestionCommentForm(request.POST,instance = ans_details)
            form.save()
            #flash message here
            return redirect('/codehub/question/'+str(ques_id)+'/details')
    else:
        ans_details = get_object_or_404(CodehubQuestionCommentModel,id = ans_id)
        ans_data = {'comment_text':ans_details.comment_text}
        form = CodehubQuestionCommentForm(initial = ans_data)
    return render(request,'codehub/question/edit_question_comment.html',{'form':form})
