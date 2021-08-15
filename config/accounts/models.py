#from config.cafe.models import CafeList
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, AbstractBaseUser
#user model 커스텀
from typing import Any, Collection, Optional, Set, Tuple, Type, TypeVar, Union
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db.models.deletion import CASCADE
from accounts.choices import *
from django.utils import timezone

#user.username 원래 있는 이름
class UserManager(BaseUserManager):
    def create_user(self, username, nickname, district, town, agree_terms, agree_marketing,  password=None):

        user = self.model(
            username = username,
            nickname = nickname,
            district = district,
            town = town,
            agree_terms=agree_terms,
            agree_marketing=agree_marketing,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, nickname, agree_terms, agree_marketing, password):
        user = self.create_user(
            username,
            nickname,
            password=password,
            district="default district",
            town = "default town",
            agree_terms=agree_terms,
            agree_marketing=agree_marketing,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user

import simplejson as json
class User(AbstractBaseUser):
    username_validator: UnicodeUsernameValidator = ...
    username = models.CharField(max_length=150, unique=True) ##########
    email = models.EmailField(blank=True)
    nickname = models.CharField(max_length=150)
    district = models.CharField(max_length=10, choices=SEOUL_DISTRICT_CHOICES)
    town = models.CharField(max_length=20, choices=SEOUL_TOWN_CHOICES)
    agree_terms = models.BooleanField(default=False)
    agree_marketing = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    
    total_visit=models.IntegerField(default=0)
    total_review=models.IntegerField(default=0)
    #한달마다 초기화
    visit_count_lastmonth = models.IntegerField(default=0) #지난 한달간 방문한 횟수 센다, 매월 초기화해준다.
    review_count_lastmonth = models.IntegerField(default=0)
    kinds_of_cafe_lastmonth = models.IntegerField(default=0)

    badge_taken=models.TextField(null=True, default=json.dumps([]))
    friends=models.TextField(null=True, default=json.dumps([]))

    objects = UserManager()

    USERNAME_FIELD ='username'
    REQUIRED_FIELDS = ['nickname', 'agree_terms', 'agree_marketing']

    def __str__(self):
        return self.username

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin

#방문한 한 카페 정보
class VisitedCafe(models.Model):
    user = models.ForeignKey(User, on_delete=CASCADE)
    cafe = models.ForeignKey('cafe.CafeList', on_delete=CASCADE, related_name='visited_cafe_list')
    visit_count = models.PositiveIntegerField(default=0)
    visit_check = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True) #카페 등록 시간
    updated_at = models.DateTimeField(auto_now=True) #갔던 카페 다시 등록

    drink_list = models.TextField(null=True, default=json.dumps([]))

    def __str__(self):
        template = '{0.cafe} {0.user} {0.visit_count}'
        return template.format(self)

    def __str__(self):
        return self.cafe.name

class Badge(models.Model):
    badge_name=models.TextField(max_length=150, unique=True)
    badge_image=models.ImageField(upload_to='../media/static/image/')
    badge_get=models.TextField(default=0)
    

#방문한 카페에서 먹은 음료 정보 -> 나중에 objects.all로 가져오기
class Drink(models.Model):
    visited_cafe = models.ForeignKey(VisitedCafe, on_delete=CASCADE)
    drinkname = models.CharField(max_length=50, choices=DRINK_CHOICES)

    created_at = models.DateTimeField(auto_now_add=True) #카페 등록 시간
    updated_at = models.DateTimeField(auto_now=True) #갔던 카페 다시 등록 

    def __str__(self):
        return self.drinkname