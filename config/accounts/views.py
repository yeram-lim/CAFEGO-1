from django import views
from django.http.response import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView
#from django.contrib.auth.models import User #회원가입을 구현하는데 있어 장고가 제공해주는 편리함
from django.urls import reverse
from django.contrib import auth
from django.views import View
from django.contrib.auth import authenticate, login, logout
from .models import * #User
from cafe.models import CafeList, Review, ReviewPhoto
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as django_logout
from . import forms
from cafe.forms import ReviewForm
from django.contrib import messages
from django.db.models import Q

# Create your views here.

def signup(request):
    if request.method == "POST":
        if request.POST["password1"] == request.POST["password2"]:
            user = User.objects.create_user(
                username=request.POST["username"], password=request.POST["password1"])
            auth.login(request, user)
            print("회원가입 성공!")
            return redirect('/accounts/') #home 페이지 따로 만들어야 댐! url 이름이 home 이어야 댐!
        return render(request, 'accounts/signup.html')
    #실패시 안넘어감
    return render(request, 'accounts/signup.html')


###allauth 써서 필요없을 듯???
class LoginView(View):
    def get(self, request):
        form = forms.LoginForm()
        ctx = {
            "form": form,
        }
        return render(request, "accounts/login.html", ctx)

    def post(self, request):
        form = forms.LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return render(request, "accounts/home.html")

        return render(request, "accounts/login.html", {"form": form})

##allauth 써서 필요 없나??
@login_required
def logout(request):
    django_logout(request)
    return render(request, "accounts/main.html")

def main(request):
    return render(request, 'accounts/main.html')

def home(request):
    #return render(request, 'accounts/home.html')
    return render(request,'accounts/home.html')

def badge_list(request):
    badges=Badge.objects.all()
    ctx={'badges':badges}

    return render(request, 'accounts/badge_list.html', context=ctx)

import simplejson as json
def badge_taken(request):
    user=request.user

    jsonDec=json.decoder.JSONDecoder()
    myList=jsonDec.decode(user.badge_taken)
    badges=Badge.objects.all()
    taken_badges=[]
    for badge in badges:
        if badge.badge_name in myList:
            taken_badges.append(badge)   
    

    ctx={'taken_badges':taken_badges,'user':user,}
    return render(request, 'accounts/badge_taken.html', context=ctx)

def badge_untaken(request):
    user=request.user

    jsonDec=json.decoder.JSONDecoder()
    myList=jsonDec.decode(user.badge_taken)
    badges=Badge.objects.all()
    taken_badges=[]
    for badge in badges:
        if not badge.badge_name in myList:
            taken_badges.append(badge) 

    ctx={'taken_badges':taken_badges, 'user':user,}
    return render(request, 'accounts/badge_untaken.html', context=ctx)

def user_cafe_map(request):
    return render(request, 'accounts/user_cafe_map.html')

def user_detail(request):
    return render(request, 'accounts/detail.html')

def rank_detail(request):
    return render(request, 'accounts/rank_detail.html')

def rank_list(request):
    ##총 방문 랭킹
    users=User.objects.all()
    for visit_user in users:
        visit_user.total_visit=0
        visit_cafes=VisitedCafe.objects.filter(user=visit_user)
        for cafe in visit_cafes:
            visit_user.total_visit+=cafe.visit_count
        
    users.order_by('-total_visit')
    ctx={
        'users':users
    }

    return render(request, 'accounts/rank_list.html', context=ctx)

@login_required
def enroll_home(request):
    return render(request, "accounts/enroll_home.html")

class EnrollNewCafeListView(ListView):
    model = VisitedCafe
    paginate_by = 15
    template_name = 'accounts/enroll_new_cafe.html'
    context_object_name = 'new_cafe_list'

    #검색기능
    def get_queryset(self):
        search_keyword = self.request.GET.get('q', '')
        search_type = self.request.GET.get('type', '') 
        visited_cafe_list = VisitedCafe.objects.filter(user=self.request.user).order_by('-id')
        
        names_to_exclude = [o.cafe for o in visited_cafe_list] 
        new_cafe_list = CafeList.objects.exclude(name__in=names_to_exclude)

        if search_keyword:
            if len(search_keyword) > 1:
                if search_type == 'name':
                    search_cafe_list = new_cafe_list.filter(name__icontains=search_keyword)
                elif search_type == 'address':
                    search_cafe_list = new_cafe_list.filter(address__icontains=search_keyword)
                elif search_type == 'all':
                    search_cafe_list = new_cafe_list.filter(Q(name__icontains=search_keyword) | Q(address__icontains=search_keyword))
                return search_cafe_list
            else:
                messages.error(self.request, '2글자 이상 입력해주세요.')
        return new_cafe_list

    #하단부에 페이징 처리
    #Django Paginator를 사용하여 간단하게 페이징처리를 구현할 수 있지만 
    #하단부의 페이지 숫자 범위를 커스텀하기 위해 
    #get_context_data 메소드로 페이지 숫자 범위 Context를 생성하여 템플릿에 전달한다.
    def get_context_data(self, **kwargs):
        #pk값 얻어옴, *kwargs는 키워드된 n개의 변수들을 함수의 인자로 보낼 때 사용
        context = super().get_context_data(**kwargs)
        paginator = context['paginator']
        #10번째 버튼?
        page_numbers_range = 10
        #page_range():(1부터 시작하는)페이지 리스트 반환 
        max_index = len(paginator.page_range)

        page = self.request.GET.get('page')
        current_page = int(page) if page else 1

        start_index = int((current_page - 1) / page_numbers_range) * page_numbers_range
        end_index = start_index + page_numbers_range
        if end_index >= max_index:
            end_index = max_index

        page_range = paginator.page_range[start_index:end_index]
        context['page_range'] = page_range

        ##
        search_keyword = self.request.GET.get('q', '')
        search_type = self.request.GET.get('type', '') 

        if len(search_keyword) > 1:
            context['q'] = search_keyword
        context['type'] = search_type

        return context

class EnrollVisitedCafeListView(ListView):
    model = VisitedCafe
    paginate_by = 5
    template_name = 'accounts/enroll_visited_cafe.html'
    context_object_name = 'visited_cafe_list'

    #검색 기능
    def get_queryset(self):
        search_keyword = self.request.GET.get('q', '')
        search_type = self.request.GET.get('type', '') 
        visited_cafe_list = VisitedCafe.objects.filter(user=self.request.user).order_by('id')#나중에 ㄱㄴㄷ 순으로 바꿀?

        if search_keyword:
            if len(search_keyword) > 1:
                if search_type == 'name':
                    search_cafe_list = visited_cafe_list.filter(name__icontains=search_keyword)
                elif search_type == 'address':
                    search_cafe_list = visited_cafe_list.filter(address__icontains=search_keyword)
                elif search_type == 'all':
                    search_cafe_list = visited_cafe_list.filter(Q(name__icontains=search_keyword) | Q(address__icontains=search_keyword))
                return search_cafe_list
            else:
                messages.error(self.request, '2글자 이상 입력해주세요.')
        return visited_cafe_list

    #하단부에 페이징 처리
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paginator = context['paginator']
        page_numbers_range = 5
        max_index = len(paginator.page_range)

        page = self.request.GET.get('page')
        current_page = int(page) if page else 1

        start_index = int((current_page - 1) / page_numbers_range) * page_numbers_range
        end_index = start_index + page_numbers_range
        if end_index >= max_index:
            end_index = max_index

        page_range = paginator.page_range[start_index:end_index]
        context['page_range'] = page_range

        search_keyword = self.request.GET.get('q', '')
        search_type = self.request.GET.get('type', '') 

        if len(search_keyword) > 1:
            context['q'] = search_keyword
        context['type'] = search_type

        return context

def mypage(request, pk):

    visit_cafes=VisitedCafe.objects.filter(user=request.user)
    user=request.user

    jsonDec=json.decoder.JSONDecoder()

    total_drink = []
    total_drink_dic = {}

    for v_cafe in visit_cafes:
        #내가 마신 음료들
        my_drinks = jsonDec.decode(v_cafe.drink_list) #visit_cafes가 여러개인데 가능한가??
        
        drink_list = []
        for drink in my_drinks:#각 음료들
            #if drink.drinkname not in my_drink:#내가 마신 음료에 없다면
            drink_list.append(drink)

        total_drink.append(drink_list)# 각각에 모든 음료 데이터들이 들어감,,,
        total_drink_dic[v_cafe] = drink_list

    owner=User.objects.get(id=pk)
    print("vcafe:", visit_cafes)
    
    print("total drink:", total_drink)#
    print("total drink dic:", total_drink_dic)#
    print("total drink dic type:", type(total_drink_dic))#

        #drink_list = Drink.objects.get(visited_cafe=cafe)#되나?
    
    #print("drink", drink)
    #print(drink_list.drinkname)
    jsonDec=json.decoder.JSONDecoder()
    badgeList=jsonDec.decode(owner.badge_taken)
    friendsList=jsonDec.decode(owner.friends)

    excludesList=jsonDec.decode(user.friends)
    names_to_exclude = [o for o in excludesList]
    names_to_exclude.append(user.nickname)

    users=User.objects.all()
    friends=[]
    for user in users:
        if user.nickname in friendsList:
            friends.append(user)
        
    myList=jsonDec.decode(user.badge_taken)
    badges=Badge.objects.all()
    taken_badges=[]
    for badge in badges:
        if badge.badge_name in badgeList:
            taken_badges.append(badge) 

    total_badge_count = len(taken_badges)
    total_visit = 0
    for cafe in visit_cafes:
        total_visit += cafe.visit_count

    my_all_review = Review.objects.filter(username=request.user)
    all_review_count = len(my_all_review)
    
    ctx={
        'owner':owner,
        'taken_badges':taken_badges,
        'visit_cafes':visit_cafes,
        'friends':friends,
        # 'drink_list' :drink_list,
        'drink_list' :total_drink,
        'drink_list_dic' :total_drink_dic,
        'total_visit':total_visit,
        'total_badge_count':total_badge_count,
        'names_to_exclude':names_to_exclude,
        'all_review_count': all_review_count,
    }

    return render(request, 'accounts/mypage.html', context=ctx)

class MyCafeReviewListView(ListView):
    model = Review
    paginate_by = 5
    template_name = 'accounts/myreview_list.html'
    context_object_name = 'my_all_review'

    def get_queryset(self):
        #여기서 위에서 지정한 모델을 필터링하는 것. 어떤 객체를 보낼지 최종적으로 보낸다.
        return Review.objects.filter(username=self.request.user)

    # paginate
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paginator = context['paginator']
        page_numbers_range = 10
        max_index = len(paginator.page_range)

        page = self.request.GET.get('page')
        current_page = int(page) if page else 1

        start_index = int((current_page - 1) / page_numbers_range) * page_numbers_range
        end_index = start_index + page_numbers_range
        if end_index >= max_index:
            end_index = max_index

        page_range = paginator.page_range[start_index:end_index]
        context['page_range'] = page_range

        search_keyword = self.request.GET.get('q', '')
        search_type = self.request.GET.get('type', '') 

        if len(search_keyword) > 1:
            context['q'] = search_keyword
        context['type'] = search_type

        return context

def review_update(request, pk):
    myreview = get_object_or_404(Review, id=pk)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=myreview)
        if form.is_valid():
            myreview = form.save(commit=False)
            myreview.username = request.user
            myreview.cafe = CafeList.objects.get(pk=pk)
            myreview = form.save()

        for img in request.FILES.getlist('imgs'):
            photo = ReviewPhoto()
            photo.review = myreview
            photo.review_cafe = myreview.cafe
            photo.image = img
            photo.save()
        
        cafe = CafeList.objects.get(pk=myreview.cafe.id)
        return redirect('cafe:review_list', cafe.id)
    else:
        #instance=myreview: 원래 속에 있던 데이터를 넣은 채 가져다 두기
        form = ReviewForm(instance=myreview)
        cafe_name = CafeList.objects.get(pk=pk)
        reviewer = request.user
        ctx = {'form': form, 'cafe_name': cafe_name, 'reviewer': reviewer}
        return render(request, 'cafe/review_form.html', ctx)

from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def visit_register(request):

    if request.method == 'POST':
        req_post = request.POST
        str_cafename = req_post.__getitem__('cafename')
        str_drinkname = req_post.__getitem__('beverage')

        v_cafe = VisitedCafe()
        v_cafe.user = request.user
        v_cafe.cafe = CafeList.objects.get(name=str_cafename)
        v_cafe.visit_check = True
        v_cafe.visit_count += 1

        drink = Drink()
        drink.visited_cafe = v_cafe
        drink.drinkname = str_drinkname
        
        jsonDec=json.decoder.JSONDecoder()
        drinkList=jsonDec.decode(v_cafe.drink_list)
        drinkList.append(str_drinkname)
        v_cafe.drink_list=json.dumps(drinkList)
        
        v_cafe.save()
        drink.save()

    return redirect('enroll_new_cafe')


@csrf_exempt
def visited_register(request):

    if request.method == 'POST':
        req_post = request.POST
        str_cafename = req_post.__getitem__('cafename')
        str_drinkname = req_post.__getitem__('beverage')
        print("drinkname:", str_drinkname)

        this_cafe = CafeList.objects.get(name=str_cafename)#전체 카페 중 그 카페
        v_cafe = VisitedCafe.objects.get(cafe=this_cafe)
        
        v_cafe.visit_count += 1

        drink = Drink.objects.get(visited_cafe=v_cafe)#이전에 등록된 것 근데 이제 필요없을듯,,,

        jsonDec=json.decoder.JSONDecoder()
        drinkList=jsonDec.decode(v_cafe.drink_list)

        drinkList.append(str_drinkname)
        v_cafe.drink_list=json.dumps(drinkList)

        v_cafe.save()
        drink.save()

    return redirect('enroll_visited_cafe')

def addfriend(request, pk):
    user=request.user
    jsonDec=json.decoder.JSONDecoder()
    friendsList=jsonDec.decode(user.friends)
    target=User.objects.get(id=pk)
    friendsList.append(target.nickname)

    user.friends=json.dumps(friendsList)
    user.save()

    return redirect('mypage',pk)

def deletefriend(request, pk):
    user=request.user
    jsonDec=json.decoder.JSONDecoder()
    friendsList=jsonDec.decode(user.friends)
    target=User.objects.get(id=pk)
    friendsList.remove(target.nickname)

    user.friends=json.dumps(friendsList)
    user.save()

    return redirect('mypage',pk)

def friend_search(request):

    return render(request, 'accounts/friend_search')


class FriendSearchListView(ListView):
    model = User
    paginate_by = 15
    template_name = 'accounts/friend_search.html'
    context_object_name = 'user_list'

    #검색기능
    def get_queryset(self):
        search_keyword = self.request.GET.get('q', '')
        search_type = self.request.GET.get('type', '') 
        user=self.request.user
        jsonDec=json.decoder.JSONDecoder()
        friendsList=jsonDec.decode(user.friends)
        user_list=User.objects.all()
        
        names_to_exclude = [o for o in friendsList]
        names_to_exclude.append(user.nickname)
        user_list = User.objects.exclude(nickname__in=names_to_exclude)
        search_user_list=[]

        if search_keyword:
            if len(search_keyword) > 1:
                if search_type == 'nickname':
                    search_user_list = user_list.filter(nickname__icontains=search_keyword)
                elif search_type == 'town':
                    search_user_list = user_list.filter(town__icontains=search_keyword)
                elif search_type == 'all':
                    search_user_list = user_list.filter(Q(nickname__icontains=search_keyword) | Q(town__icontains=search_keyword))
                return search_user_list
            else:
                messages.error(self.request, '2글자 이상 입력해주세요.')
        return user_list

    #하단부에 페이징 처리
    #Django Paginator를 사용하여 간단하게 페이징처리를 구현할 수 있지만 
    #하단부의 페이지 숫자 범위를 커스텀하기 위해 
    #get_context_data 메소드로 페이지 숫자 범위 Context를 생성하여 템플릿에 전달한다.
    def get_context_data(self, **kwargs):
        #pk값 얻어옴, *kwargs는 키워드된 n개의 변수들을 함수의 인자로 보낼 때 사용
        context = super().get_context_data(**kwargs)
        paginator = context['paginator']
        #10번째 버튼?
        page_numbers_range = 10
        #page_range():(1부터 시작하는)페이지 리스트 반환 
        max_index = len(paginator.page_range)

        page = self.request.GET.get('page')
        current_page = int(page) if page else 1

        start_index = int((current_page - 1) / page_numbers_range) * page_numbers_range
        end_index = start_index + page_numbers_range
        if end_index >= max_index:
            end_index = max_index

        page_range = paginator.page_range[start_index:end_index]
        context['page_range'] = page_range

        ##
        search_keyword = self.request.GET.get('q', '')
        search_type = self.request.GET.get('type', '') 

        if len(search_keyword) > 1:
            context['q'] = search_keyword
        context['type'] = search_type

        return context

@csrf_exempt
def friend_register(request):

    if request.method == 'POST':
        # 프렌드리스트 해체 및 추가 / 저장
        req_post = request.POST
        str_friendname = req_post.__getitem__('friendname')

        user=request.user

        jsonDec=json.decoder.JSONDecoder()
        friendsList=jsonDec.decode(user.friends)
        friendsList.append(str_friendname)
        user.friends=json.dumps(friendsList)
        user.save()

    return redirect('friend_search')