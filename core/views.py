from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import FileResponse, JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator, EmptyPage
from django.contrib import messages
import json
import re
import logging
from .models import *
from .forms import *

# Set up logging
logger = logging.getLogger(__name__)

# ===== ENHANCED AI CHAT PROCESSOR =====

class AdvancedAIChatProcessor:
    def __init__(self):
        self.common_question_patterns = {
            'how_to_solve': ['how to solve', 'how do i solve', 'steps to solve', 'method to solve'],
            'formula': ['formula for', 'equation for', 'what is the formula'],
            'definition': ['what is', 'define', 'meaning of', 'explain what is'],
            'explanation': ['how does', 'why does', 'explain how', 'describe the process'],
            'difference': ['difference between', 'distinguish between', 'compare and contrast'],
            'example': ['example of', 'instance of', 'sample of', 'illustrate'],
            'calculation': ['calculate', 'compute', 'find the value', 'solve for']
        }
    
    def build_subject_keyword_map(self, subjects):
        """Build dynamic keyword mapping from actual subject names and content"""
        subject_keyword_map = {}
        
        for subject in subjects:
            subject_name_lower = subject.name.lower()
            subject_keyword_map[subject] = {
                'primary_keywords': self._extract_keywords_from_name(subject_name_lower),
                'extended_keywords': self._get_extended_keywords_for_subject(subject),
                'question_patterns': self._get_question_patterns_for_subject(subject)
            }
        
        return subject_keyword_map
    
    def _extract_keywords_from_name(self, subject_name):
        """Extract meaningful keywords from subject name"""
        stop_words = ['and', 'the', 'of', 'for', 'in', 'with', 'basic', 'advanced', 'fundamental']
        words = re.findall(r'\w+', subject_name)
        keywords = [word for word in words if word.lower() not in stop_words and len(word) > 2]
        return set(keywords)
    
    def _get_extended_keywords_for_subject(self, subject):
        """Get extended keywords from study materials and FAQs"""
        extended_keywords = set()
        
        # Get keywords from study materials
        material_keywords = StudyMaterial.objects.filter(
            subject=subject
        ).exclude(keywords__isnull=True).exclude(keywords='').values_list('keywords', flat=True)
        
        for keyword_string in material_keywords:
            if keyword_string:
                keywords = [kw.strip().lower() for kw in keyword_string.split(',')]
                extended_keywords.update(keywords)
        
        # Get keywords from FAQs
        faq_keywords = FAQ.objects.filter(
            subject=subject
        ).exclude(keywords__isnull=True).exclude(keywords='').values_list('keywords', flat=True)
        
        for keyword_string in faq_keywords:
            if keyword_string:
                keywords = [kw.strip().lower() for kw in keyword_string.split(',')]
                extended_keywords.update(keywords)
        
        # Extract terms from titles and descriptions
        material_terms = StudyMaterial.objects.filter(subject=subject).values_list('title', 'description')
        for title, description in material_terms:
            if title:
                extended_keywords.update(self._extract_keywords_from_text(title))
            if description:
                extended_keywords.update(self._extract_keywords_from_text(description))
        
        return extended_keywords
    
    def _get_question_patterns_for_subject(self, subject):
        """Get subject-specific question patterns"""
        subject_name_lower = subject.name.lower()
        
        base_patterns = {
            'definition': ['what is', 'define', 'meaning of'],
            'explanation': ['explain', 'how does', 'why does'],
            'example': ['example of', 'instance of', 'sample of']
        }
        
        # Add subject-specific patterns
        if any(word in subject_name_lower for word in ['math', 'mathematics', 'algebra', 'calculus']):
            base_patterns.update({
                'solve': ['how to solve', 'solve for', 'find the value'],
                'formula': ['formula for', 'equation for', 'what is the formula'],
                'proof': ['prove that', 'show that', 'demonstrate']
            })
        elif any(word in subject_name_lower for word in ['science', 'physics', 'chemistry', 'biology']):
            base_patterns.update({
                'process': ['how does work', 'process of', 'mechanism of'],
                'experiment': ['experiment for', 'how to test', 'demonstrate'],
                'theory': ['theory of', 'principle of', 'law of']
            })
        elif any(word in subject_name_lower for word in ['english', 'language', 'grammar', 'literature']):
            base_patterns.update({
                'grammar': ['rule for', 'how to use', 'when to use'],
                'writing': ['how to write', 'tips for writing', 'structure of'],
                'analysis': ['analyze', 'interpret', 'what does mean']
            })
        
        return base_patterns
    
    def _extract_keywords_from_text(self, text):
        """Extract meaningful keywords from text"""
        if not text:
            return set()
        
        text_lower = text.lower()
        words = re.findall(r'\w+', text_lower)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        keywords = {word for word in words if len(word) > 3 and word not in stop_words}
        return keywords
    
    def detect_subject(self, question, available_subjects):
        """Enhanced subject detection using actual subject names and keywords"""
        question_lower = question.lower()
        
        # Build dynamic keyword map
        subject_keyword_map = self.build_subject_keyword_map(available_subjects)
        
        subject_scores = {}
        
        for subject in available_subjects:
            subject_scores[subject] = 0
            keyword_data = subject_keyword_map[subject]
            
            # 1. Direct subject name match (highest priority)
            subject_name_lower = subject.name.lower()
            if subject_name_lower in question_lower:
                subject_scores[subject] += 10
            
            # 2. Primary keyword matching
            for keyword in keyword_data['primary_keywords']:
                if keyword in question_lower:
                    subject_scores[subject] += 5
            
            # 3. Extended keyword matching
            for keyword in keyword_data['extended_keywords']:
                if keyword in question_lower:
                    subject_scores[subject] += 3
            
            # 4. Question pattern matching
            for pattern_type, patterns in keyword_data['question_patterns'].items():
                for pattern in patterns:
                    if pattern in question_lower:
                        subject_scores[subject] += 2
            
            # 5. Partial word matching
            subject_words = subject_name_lower.split()
            for word in subject_words:
                if len(word) > 4 and word in question_lower:
                    subject_scores[subject] += 2
        
        # Filter and return best match
        valid_subjects = {subject: score for subject, score in subject_scores.items() if score > 0}
        
        if valid_subjects:
            best_subject = max(valid_subjects, key=valid_subjects.get)
            logger.info(f"Subject detected: {best_subject.name} (Score: {valid_subjects[best_subject]})")
            return best_subject
        
        return None
    
    def analyze_question_type(self, question):
        """Analyze the type of question for better response generation"""
        question_lower = question.lower()
        
        question_types = {
            'definition': any(word in question_lower for word in ['what is', 'define', 'meaning of', 'what does']),
            'how_to': any(word in question_lower for word in ['how to', 'how do i', 'steps to', 'method for']),
            'explanation': any(word in question_lower for word in ['explain', 'why', 'describe', 'tell me about']),
            'example': any(word in question_lower for word in ['example', 'instance', 'sample', 'illustrate']),
            'comparison': any(word in question_lower for word in ['difference between', 'compare', 'vs', 'versus']),
            'calculation': any(word in question_lower for word in ['calculate', 'solve', 'compute', 'find the value']),
        }
        
        for q_type, matches in question_types.items():
            if matches:
                return q_type
        
        return 'general'
    
    def calculate_relevance_score(self, question, content_obj):
        """Calculate comprehensive relevance score"""
        question_lower = question.lower()
        
        if hasattr(content_obj, 'content'):  # StudyMaterial
            content_text = f"{content_obj.title} {content_obj.description} {content_obj.content} {content_obj.keywords}"
        else:  # FAQ
            content_text = f"{content_obj.question} {content_obj.answer} {content_obj.keywords}"
        
        content_lower = content_text.lower()
        
        # Extract meaningful words
        question_words = set([word for word in re.findall(r'\w+', question_lower) if len(word) > 2])
        content_words = set([word for word in re.findall(r'\w+', content_lower) if len(word) > 2])
        
        if not question_words:
            return 0
        
        # 1. Keyword overlap
        common_words = question_words.intersection(content_words)
        keyword_score = len(common_words) / len(question_words)
        
        # 2. Exact phrase matching
        phrase_score = 0
        for phrase in question_lower.split('.'):
            phrase = phrase.strip()
            if len(phrase) > 10 and phrase in content_lower:
                phrase_score += 0.3
        
        # 3. Title relevance
        title_score = 0
        if hasattr(content_obj, 'title'):
            title_words = set([word for word in re.findall(r'\w+', content_obj.title.lower()) if len(word) > 2])
            title_common = question_words.intersection(title_words)
            if title_words:
                title_score = len(title_common) / len(title_words)
        
        # 4. Keyword field relevance
        keyword_field_score = 0
        if hasattr(content_obj, 'keywords') and content_obj.keywords:
            keyword_list = [kw.strip().lower() for kw in content_obj.keywords.split(',')]
            keyword_words = set()
            for kw in keyword_list:
                keyword_words.update([word for word in re.findall(r'\w+', kw) if len(word) > 2])
            
            keyword_common = question_words.intersection(keyword_words)
            if keyword_words:
                keyword_field_score = len(keyword_common) / len(keyword_words)
        
        # 5. Content type bonus
        type_bonus = 0
        if hasattr(content_obj, 'material_type'):
            if content_obj.material_type in ['theory', 'formula', 'example']:
                type_bonus = 0.1
        
        # Combine scores
        final_score = (
            keyword_score * 0.3 +
            phrase_score * 0.25 +
            title_score * 0.2 +
            keyword_field_score * 0.2 +
            type_bonus * 0.05
        )
        
        return min(final_score, 1.0)
    
    def find_best_matches(self, question, subject, student_profile):
        """Find the best matching content"""
        materials = StudyMaterial.objects.filter(
            subject=subject,
            teacher__classes=student_profile.class_enrolled
        ).select_related('teacher', 'subject')
        
        faqs = FAQ.objects.filter(subject=subject).select_related('teacher', 'subject')
        
        all_matches = []
        
        # Search in study materials
        for material in materials:
            score = self.calculate_relevance_score(question, material)
            if score > 0.1:
                all_matches.append({
                    'type': 'material',
                    'content': material,
                    'score': score
                })
        
        # Search in FAQs
        for faq in faqs:
            score = self.calculate_relevance_score(question, faq)
            if score > 0.1:
                all_matches.append({
                    'type': 'faq',
                    'content': faq,
                    'score': score
                })
        
        # Sort by score
        all_matches.sort(key=lambda x: x['score'], reverse=True)
        return all_matches[:5]
    
    def generate_response(self, question, subject, student_profile):
        """Generate comprehensive response"""
        matches = self.find_best_matches(question, subject, student_profile)
        question_type = self.analyze_question_type(question)
        
        if matches:
            return self._generate_response_from_matches(question, matches, question_type, subject)
        else:
            return self._generate_fallback_response(question, subject, student_profile, question_type)
    
    def _generate_response_from_matches(self, question, matches, question_type, subject):
        """Generate response using best matches"""
        best_match = matches[0]
        
        if best_match['type'] == 'material':
            response = self._format_material_response(best_match['content'], question_type)
        else:
            response = self._format_faq_response(best_match['content'])
        
        # Add related content
        if len(matches) > 1:
            response += self._add_related_content(matches[1:3])
        
        # Add confidence indicator
        confidence = min(best_match['score'] * 2, 1.0)
        confidence_text = self._get_confidence_text(confidence)
        response += f"\n\n🎯 *{confidence_text}*"
        
        return response
    
    def _get_confidence_text(self, confidence):
        """Get confidence text"""
        if confidence > 0.7:
            return "High Confidence - This answer is well-supported by study materials"
        elif confidence > 0.4:
            return "Medium Confidence - This answer is based on related content"
        else:
            return "Low Confidence - This might be related but please verify with your teacher"
    
    def _format_material_response(self, material, question_type):
        """Format response from study material"""
        response_parts = []
        
        response_parts.append(f"📚 **Based on: {material.title}**")
        
        # Content based on question type
        if material.content:
            if question_type == 'definition':
                response_parts.append(f"\n{material.content}")
            elif question_type == 'how_to':
                content = self._format_as_steps(material.content)
                response_parts.append(f"\n{content}")
            else:
                response_parts.append(f"\n{material.content}")
        elif material.description:
            response_parts.append(f"\n{material.description}")
        
        # Add material type context
        type_emojis = {
            'theory': '📖 Theoretical Concept', 
            'formula': '🧮 Formula & Equation',
            'example': '💡 Solved Example',
            'notes': '📝 Study Notes', 
            'assignment': '📋 Practice Assignment',
            'quiz': '❓ Quiz Question'
        }
        emoji_text = type_emojis.get(material.material_type, '📄 Study Material')
        response_parts.append(f"\n\n{emoji_text}")
        
        # Show keywords if available
        if material.keywords:
            response_parts.append(f"\n🏷️ *Keywords: {material.keywords}*")
        
        return "\n".join(response_parts)
    
    def _format_faq_response(self, faq):
        """Format response from FAQ"""
        response = f"❓ **Question:** {faq.question}\n\n"
        response += f"💡 **Answer:** {faq.answer}"
        
        if faq.keywords:
            response += f"\n\n🏷️ *Related topics: {faq.keywords}*"
        
        return response
    
    def _format_as_steps(self, content):
        """Format content as step-by-step instructions"""
        lines = content.split('\n')
        step_content = []
        step_count = 1
        
        for line in lines:
            line = line.strip()
            if line and len(line) > 10:
                step_content.append(f"{step_count}. {line}")
                step_count += 1
        
        if len(step_content) > 1:
            return "\n".join(step_content)
        else:
            return content
    
    def _add_related_content(self, related_matches):
        """Add related content suggestions"""
        if not related_matches:
            return ""
        
        response = "\n\n🔍 **Related content you might find helpful:**"
        
        for match in related_matches:
            if match['type'] == 'material':
                response += f"\n• {match['content'].title} ({match['content'].get_material_type_display()})"
            else:
                response += f"\n• Q: {match['content'].question[:60]}..."
        
        return response
    
    def _generate_fallback_response(self, question, subject, student_profile, question_type):
        """Generate intelligent fallback response"""
        response_parts = []
        
        response_parts.append(f"🤔 **I'm still learning about {subject.name}**")
        response_parts.append(f"\nI couldn't find a perfect match for your question, but here are some suggestions:")
        
        # Get available materials
        materials = StudyMaterial.objects.filter(
            subject=subject,
            teacher__classes=student_profile.class_enrolled
        )[:5]
        
        if materials.exists():
            response_parts.append(f"\n📂 **Available resources in {subject.name}:**")
            for material in materials:
                response_parts.append(f"• {material.title} ({material.get_material_type_display()})")
        
        # Get common keywords
        material_keywords = StudyMaterial.objects.filter(
            subject=subject,
            teacher__classes=student_profile.class_enrolled
        ).exclude(keywords__isnull=True).exclude(keywords='').values_list('keywords', flat=True)
        
        if material_keywords:
            all_keywords = set()
            for kw_string in material_keywords:
                keywords = [kw.strip() for kw in kw_string.split(',')]
                all_keywords.update(keywords)
            
            if all_keywords:
                sample_keywords = list(all_keywords)[:8]
                response_parts.append(f"\n🔑 **Try asking about:** {', '.join(sample_keywords)}")
        
        # Question-specific suggestions
        suggestions = self._get_question_suggestions(question_type, subject.name)
        response_parts.extend(suggestions)
        
        return "\n".join(response_parts)
    
    def _get_question_suggestions(self, question_type, subject_name):
        """Get suggestions based on question type"""
        suggestions = []
        suggestions.append(f"\n🎯 **Tips for better answers in {subject_name}:**")
        
        if question_type == 'definition':
            suggestions.extend([
                f"💡 Try: 'What is [specific term] in {subject_name}?'",
                f"💡 Try: 'Define [concept] from {subject_name}'",
                f"💡 Be more specific with the term you want defined"
            ])
        elif question_type == 'how_to':
            suggestions.extend([
                f"💡 Try: 'How to solve [specific problem] in {subject_name}?'",
                f"💡 Try: 'Steps to [process] in {subject_name}'",
                f"💡 Mention the specific method or problem type"
            ])
        elif question_type == 'explanation':
            suggestions.extend([
                f"💡 Try: 'Explain [concept] in {subject_name} in detail'",
                f"💡 Try: 'Why does [phenomenon] occur in {subject_name}?'",
                f"💡 Specify which aspect you want explained"
            ])
        else:
            suggestions.extend([
                f"💡 Try being more specific about the topic",
                f"💡 Mention key terms from {subject_name}",
                f"💡 Ask about specific concepts you're studying"
            ])
        
        return suggestions

# Initialize AI processor
ai_processor = AdvancedAIChatProcessor()

# ===== AUTHENTICATION VIEWS =====

def index(request):
    return render(request, 'index.html')

def student_register(request):
    if request.method == 'POST':
        user_form = CustomUserForm(request.POST)
        student_form = StudentProfileForm(request.POST)
        
        if user_form.is_valid() and student_form.is_valid():
            try:
                user = user_form.save(commit=False)
                user.user_type = 'student'
                user.set_password(user_form.cleaned_data['password'])
                user.save()
                
                student_profile = student_form.save(commit=False)
                student_profile.user = user
                student_profile.save()
                
                login(request, user)
                messages.success(request, f'Welcome {user.first_name}! Your account has been created successfully.')
                return redirect('student_dashboard')
                
            except Exception as e:
                messages.error(request, f'An error occurred during registration: {str(e)}')
        else:
            all_errors = []
            for field, errors in user_form.errors.items():
                for error in errors:
                    all_errors.append(f"{field}: {error}")
            for field, errors in student_form.errors.items():
                for error in errors:
                    all_errors.append(f"{field}: {error}")
            
            if all_errors:
                messages.error(request, "Please correct the errors below.")
    
    else:
        user_form = CustomUserForm()
        student_form = StudentProfileForm()
    
    return render(request, 'student/register.html', {
        'user_form': user_form,
        'student_form': student_form
    })

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user_type = request.POST.get('user_type', 'student')
        
        user = authenticate(request, username=username, password=password)
        
        if user is None:
            try:
                user = CustomUser.objects.get(username=username)
                if not user.check_password(password):
                    messages.error(request, 'Invalid password.')
                    return render(request, 'login.html')
            except CustomUser.DoesNotExist:
                messages.error(request, 'User does not exist.')
                return render(request, 'login.html')
        
        if user is not None:
            if user.user_type == user_type:
                if user.is_active:
                    login(request, user)
                    messages.success(request, f'Welcome back, {user.first_name}!')
                    
                    next_url = request.POST.get('next') or request.GET.get('next')
                    if next_url:
                        return redirect(next_url)
                    
                    if user.user_type == 'student':
                        return redirect('student_dashboard')
                    elif user.user_type == 'teacher':
                        return redirect('teacher_dashboard')
                    elif user.user_type == 'admin':
                        return redirect('admin_dashboard')
                else:
                    messages.error(request, 'Your account is inactive.')
            else:
                messages.error(request, f'Please use {user.user_type} login.')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html', {'next': request.GET.get('next', '')})

def standalone_login(request):
    return user_login(request)

def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('index')

# ===== DASHBOARD VIEWS =====

@login_required
def student_dashboard(request):
    if request.user.user_type != 'student':
        messages.warning(request, 'You need a student account to access this page.')
        return redirect('index')
    
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
        subjects = student_profile.class_enrolled.subjects.all()
        
        recent_chats = ChatHistory.objects.filter(student=student_profile).order_by('-created_at')[:5]
        
        return render(request, 'student/dashboard.html', {
            'student_profile': student_profile,
            'subjects': subjects,
            'recent_chats': recent_chats
        })
    except StudentProfile.DoesNotExist:
        messages.error(request, 'Student profile not found. Please contact administrator.')
        return redirect('index')

@login_required
@user_passes_test(lambda u: u.user_type == 'teacher')
def teacher_dashboard(request):
    try:
        teacher_profile = TeacherProfile.objects.get(user=request.user)
        materials = StudyMaterial.objects.filter(teacher=teacher_profile).order_by('-created_at')[:5]
        faqs = FAQ.objects.filter(teacher=teacher_profile).order_by('-created_at')[:5]
        
        total_materials = StudyMaterial.objects.filter(teacher=teacher_profile).count()
        total_faqs = FAQ.objects.filter(teacher=teacher_profile).count()
        total_subjects = teacher_profile.subjects.count()
        
        return render(request, 'teacher/dashboard.html', {
            'teacher_profile': teacher_profile,
            'materials': materials,
            'faqs': faqs,
            'total_materials': total_materials,
            'total_faqs': total_faqs,
            'total_subjects': total_subjects
        })
    except TeacherProfile.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('index')

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def admin_dashboard(request):
    stats = {
        'total_students': StudentProfile.objects.count(),
        'total_teachers': TeacherProfile.objects.filter(is_active=True).count(),
        'total_subjects': Subject.objects.count(),
        'total_classes': Class.objects.count(),
        'total_materials': StudyMaterial.objects.count(),
        'total_faqs': FAQ.objects.count(),
    }
    return render(request, 'admin/dashboard.html', {'stats': stats})

# ===== STUDY MATERIALS & FAQ VIEWS =====

@login_required
@user_passes_test(lambda u: u.user_type == 'teacher')
def add_study_material(request):
    teacher_profile = TeacherProfile.objects.get(user=request.user)
    
    if request.method == 'POST':
        form = StudyMaterialForm(request.POST, request.FILES)
        if form.is_valid():
            material = form.save(commit=False)
            material.teacher = teacher_profile
            material.save()
            messages.success(request, f'Study material "{material.title}" has been added successfully!')
            return redirect('teacher_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StudyMaterialForm()
        form.fields['subject'].queryset = teacher_profile.subjects.all()
    
    return render(request, 'teacher/add_material.html', {'form': form})

@login_required
@user_passes_test(lambda u: u.user_type == 'teacher')
def add_faq(request):
    teacher_profile = TeacherProfile.objects.get(user=request.user)
    
    if request.method == 'POST':
        form = FAQForm(request.POST)
        if form.is_valid():
            faq = form.save(commit=False)
            faq.teacher = teacher_profile
            faq.save()
            messages.success(request, f'FAQ has been added successfully!')
            return redirect('teacher_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = FAQForm()
        form.fields['subject'].queryset = teacher_profile.subjects.all()
    
    return render(request, 'teacher/add_faq.html', {'form': form})

# ===== ENHANCED AI CHAT VIEW =====

@csrf_exempt
@login_required
def chat_with_ai(request):
    """Enhanced AI chat endpoint with advanced subject detection"""
    if request.method == 'POST' and request.user.user_type == 'student':
        try:
            data = json.loads(request.body)
            question = data.get('question', '').strip()
            
            if not question:
                return JsonResponse({'error': 'Please enter a question'}, status=400)
            
            if len(question) < 3:
                return JsonResponse({'error': 'Please enter a more detailed question'}, status=400)
            
            logger.info(f"Chat request from {request.user}: {question}")
            
            student_profile = StudentProfile.objects.get(user=request.user)
            subjects = student_profile.class_enrolled.subjects.all()
            
            if not subjects.exists():
                return JsonResponse({
                    'error': 'No subjects found for your class. Please contact administrator.'
                }, status=400)
            
            # Detect subject using advanced processor
            subject = ai_processor.detect_subject(question, subjects)
            
            if subject:
                logger.info(f"Detected subject: {subject.name}")
                
                # Generate response
                response = ai_processor.generate_response(question, subject, student_profile)
                
                # Calculate confidence
                matches = ai_processor.find_best_matches(question, subject, student_profile)
                confidence = matches[0]['score'] if matches else 0.3
                
                # Save chat history
                chat = ChatHistory.objects.create(
                    student=student_profile,
                    question=question,
                    answer=response,
                    subject=subject,
                    confidence_score=confidence
                )
                
                return JsonResponse({
                    'answer': response,
                    'subject': subject.name,
                    'confidence': round(confidence, 2),
                    'success': True
                })
            
            else:
                # No subject detected
                response = generate_multi_subject_response(question, subjects)
                
                chat = ChatHistory.objects.create(
                    student=student_profile,
                    question=question,
                    answer=response,
                    confidence_score=0.1
                )
                
                return JsonResponse({
                    'answer': response,
                    'subject': 'Multiple Subjects',
                    'confidence': 0.1,
                    'success': True
                })
        
        except StudentProfile.DoesNotExist:
            logger.error(f"StudentProfile not found for user: {request.user}")
            return JsonResponse({
                'error': 'Student profile not found. Please contact administrator.'
            }, status=404)
        
        except Exception as e:
            logger.error(f"Chat error: {str(e)}", exc_info=True)
            return JsonResponse({
                'error': 'Sorry, I encountered an error while processing your question. Please try again.'
            }, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def generate_multi_subject_response(question, subjects):
    """Generate response when no specific subject is detected"""
    subject_names = [subject.name for subject in subjects]
    
    # Build keyword suggestions
    keyword_suggestions = []
    for subject in subjects:
        primary_keywords = ai_processor._extract_keywords_from_name(subject.name.lower())
        if primary_keywords:
            keyword_suggestions.extend(list(primary_keywords))
    
    response = [
        "🎯 **I'm not sure which subject you're asking about.**",
        f"\n**Your available subjects are:** {', '.join(subject_names)}",
    ]
    
    if keyword_suggestions:
        response.append(f"\n**Key topics available:** {', '.join(set(keyword_suggestions))[:100]}...")
    
    response.extend([
        "\n**Please try one of these formats:**",
        "• Start with the subject name: '[Subject]: [Your question]'",
        "• Include key subject terms in your question",
        "• Be more specific about the topic",
        "\n**Examples that work well:**",
    ])
    
    # Add examples based on actual subjects
    for subject in subjects[:3]:
        subject_examples = {
            'math': f"• '{subject.name}: How to solve quadratic equations?'",
            'science': f"• '{subject.name}: Explain the process of photosynthesis'",
            'english': f"• '{subject.name}: What are the rules for using tenses?'",
            'physics': f"• '{subject.name}: Explain Newton's laws of motion'",
            'chemistry': f"• '{subject.name}: What is chemical bonding?'"
        }
        
        for key, example in subject_examples.items():
            if key in subject.name.lower():
                response.append(example)
                break
        else:
            response.append(f"• '{subject.name}: Explain key concepts in {subject.name}'")
    
    response.append("\n💡 **Tip:** The more specific your question, the better I can help!")
    
    return "\n".join(response)

# ===== STUDY MATERIALS API VIEWS =====

@login_required
def get_study_materials(request):
    """API endpoint to get study materials for students"""
    if request.user.user_type != 'student':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
        
        materials = StudyMaterial.objects.all().select_related('subject', 'teacher').order_by('-created_at')
        
        # Apply filters
        search_query = request.GET.get('search', '')
        if search_query:
            materials = materials.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(subject__name__icontains=search_query) |
                Q(keywords__icontains=search_query)
            )
        
        subject_filter = request.GET.get('subject', '')
        if subject_filter:
            materials = materials.filter(subject__name=subject_filter)
        
        type_filter = request.GET.get('type', '')
        if type_filter:
            materials = materials.filter(material_type=type_filter)
        
        # Pagination
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 6))
        
        paginator = Paginator(materials, limit)
        
        try:
            materials_page = paginator.page(page)
        except EmptyPage:
            materials_page = paginator.page(paginator.num_pages)
        
        # Serialize materials
        materials_data = []
        for material in materials_page:
            file_size = material.file.size if material.file else 0
            file_url = material.file.url if material.file else material.external_url
            
            materials_data.append({
                'id': material.id,
                'title': material.title,
                'description': material.description,
                'file_type': material.material_type,
                'file_size': file_size,
                'file_url': file_url,
                'subject': material.subject.name,
                'teacher': f"{material.teacher.user.first_name} {material.teacher.user.last_name}".strip(),
                'created_at': material.created_at.strftime("%b %d, %Y"),
                'keywords': material.keywords.split(',') if material.keywords else []
            })
        
        return JsonResponse({
            'materials': materials_data,
            'has_more': materials_page.has_next(),
            'total_pages': paginator.num_pages,
            'current_page': page,
            'total_count': paginator.count
        })
        
    except StudentProfile.DoesNotExist:
        return JsonResponse({'error': 'Student profile not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def view_study_material(request, material_id):
    """View a specific study material"""
    if request.user.user_type != 'student':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        material = StudyMaterial.objects.get(id=material_id)
        
        material_data = {
            'id': material.id,
            'title': material.title,
            'description': material.description,
            'file_type': material.material_type,
            'file_url': material.file.url if material.file else material.external_url,
            'subject': material.subject.name,
            'teacher': f"{material.teacher.user.first_name} {material.teacher.user.last_name}".strip(),
            'created_at': material.created_at.strftime("%b %d, %Y"),
            'content': material.content,
            'keywords': material.keywords.split(',') if material.keywords else []
        }
        
        return JsonResponse(material_data)
        
    except StudyMaterial.DoesNotExist:
        return JsonResponse({'error': 'Study material not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def download_study_material(request, material_id):
    """Download a specific study material"""
    if request.user.user_type != 'student':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        material = StudyMaterial.objects.get(id=material_id)
        
        if material.file:
            response = FileResponse(material.file.open(), as_attachment=True, filename=material.file.name)
            return response
        elif material.external_url:
            return redirect(material.external_url)
        else:
            return JsonResponse({'error': 'No file or URL available for this material'}, status=404)
            
    except StudyMaterial.DoesNotExist:
        return JsonResponse({'error': 'Study material not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== FAQ API VIEWS =====

@login_required
def get_faqs(request):
    """API endpoint to get FAQs for students"""
    if request.user.user_type != 'student':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
        
        # Get all subjects from student's class
        student_subjects = student_profile.class_enrolled.subjects.all()
        
        # Debug information
        print(f"DEBUG: Student: {student_profile.user.username}")
        print(f"DEBUG: Student Class: {student_profile.class_enrolled}")
        print(f"DEBUG: Student Subjects: {[s.name for s in student_subjects]}")
        
        # Get ALL FAQs first to see what's available
        all_faqs_count = FAQ.objects.count()
        print(f"DEBUG: Total FAQs in database: {all_faqs_count}")
        
        # Get FAQs by subject in database
        faqs_by_subject = FAQ.objects.values('subject__name').annotate(count=Count('id'))
        print(f"DEBUG: FAQs by subject in DB: {list(faqs_by_subject)}")
        
        # Get FAQs for student's subjects
        faqs = FAQ.objects.filter(subject__in=student_subjects).select_related('subject', 'teacher').order_by('-created_at')
        
        print(f"DEBUG: FAQs found for student's subjects: {faqs.count()}")
        
        # If no FAQs found for student's specific subjects, get ALL FAQs as fallback
        if faqs.count() == 0:
            print("DEBUG: No FAQs found for student's specific subjects, falling back to all FAQs")
            faqs = FAQ.objects.all().select_related('subject', 'teacher').order_by('-created_at')
        
        # Apply search filter if provided
        search_query = request.GET.get('search', '')
        if search_query:
            faqs = faqs.filter(
                Q(question__icontains=search_query) |
                Q(answer__icontains=search_query) |
                Q(subject__name__icontains=search_query) |
                Q(keywords__icontains=search_query)
            )
            print(f"DEBUG: After search filter '{search_query}': {faqs.count()} FAQs")
        
        # Apply subject filter if provided
        subject_filter = request.GET.get('subject', '')
        if subject_filter:
            faqs = faqs.filter(subject__name=subject_filter)
            print(f"DEBUG: After subject filter '{subject_filter}': {faqs.count()} FAQs")
        
        # Get unique subjects from the actual FAQ results
        faq_subjects = Subject.objects.filter(
            id__in=faqs.values_list('subject_id', flat=True)
        ).distinct()
        
        # Pagination
        page = request.GET.get('page', 1)
        limit = request.GET.get('limit', 6)
        
        paginator = Paginator(faqs, limit)
        
        try:
            faqs_page = paginator.page(page)
        except EmptyPage:
            faqs_page = paginator.page(paginator.num_pages)
        
        # Serialize FAQs
        faqs_data = []
        for faq in faqs_page:
            faqs_data.append({
                'id': faq.id,
                'question': faq.question,
                'answer': faq.answer,
                'subject': faq.subject.name,
                'teacher': f"{faq.teacher.user.first_name} {faq.teacher.user.last_name}".strip(),
                'created_at': faq.created_at.strftime("%b %d, %Y"),
                'keywords': faq.keywords.split(',') if faq.keywords else []
            })
        
        response_data = {
            'faqs': faqs_data,
            'has_more': faqs_page.has_next(),
            'total_pages': paginator.num_pages,
            'current_page': page,
            'total_count': paginator.count,
            'available_subjects': list(faq_subjects.values_list('name', flat=True)),
            'debug_info': {
                'student_subjects': [s.name for s in student_subjects],
                'total_faqs_in_db': all_faqs_count,
                'faqs_by_subject_in_db': list(faqs_by_subject),
                'faqs_found_for_student': faqs.count()
            }
        }
        
        print(f"DEBUG: Sending response with {len(faqs_data)} FAQs")
        return JsonResponse(response_data)
        
    except StudentProfile.DoesNotExist:
        print("ERROR: Student profile not found")
        return JsonResponse({'error': 'Student profile not found'}, status=404)
    except Exception as e:
        print(f"ERROR in get_faqs: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

# ===== ANALYTICS VIEWS =====

@login_required
@user_passes_test(lambda u: u.user_type == 'teacher')
def teacher_analytics(request):
    teacher_profile = TeacherProfile.objects.get(user=request.user)
    
    chat_analytics = ChatHistory.objects.filter(
        source_material__teacher=teacher_profile
    ).values('subject__name').annotate(
        total_questions=Count('id'),
        avg_confidence=Avg('confidence_score')
    )
    
    materials_by_subject = StudyMaterial.objects.filter(
        teacher=teacher_profile
    ).values('subject__name').annotate(count=Count('id'))
    
    recent_questions = ChatHistory.objects.filter(
        source_material__teacher=teacher_profile
    ).select_related('student', 'subject').order_by('-created_at')[:10]
    
    return render(request, 'teacher/analytics.html', {
        'teacher_profile': teacher_profile,
        'chat_analytics': chat_analytics,
        'materials_by_subject': materials_by_subject,
        'recent_questions': recent_questions
    })

# ===== UTILITY VIEWS =====

@login_required
def profile(request):
    """User profile page"""
    user = request.user
    context = {'user': user}
    
    if user.user_type == 'student':
        try:
            context['student_profile'] = StudentProfile.objects.get(user=user)
        except StudentProfile.DoesNotExist:
            pass
    elif user.user_type == 'teacher':
        try:
            context['teacher_profile'] = TeacherProfile.objects.get(user=user)
        except TeacherProfile.DoesNotExist:
            pass
    
    return render(request, 'profile.html', context)

def handler404(request, exception):
    return render(request, '404.html', status=404)

def handler500(request):
    return render(request, '500.html', status=500)