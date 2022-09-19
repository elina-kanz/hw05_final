from .models import Post, Group, Comment
from django import forms


class PostForm(forms.ModelForm):
    group = forms.ModelChoiceField(Group.objects.all(), required=False)

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')

    def clean_text(self):
        data = self.cleaned_data['text']
        if data == '':
            raise forms.ValidationError('Заполните поле текста поста')
        return data


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)

    def clean_text(self):
        data = self.cleaned_data['text']
        if data == '':
            raise forms.ValidationError('Заполните поле комментария')
        return data
