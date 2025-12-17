"""
Views for Front Page management API.
"""

from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.db.models import Q

from .models import (
    SliderRevolution,
    Slide,
    SlideLayer,
    HomepageSection,
    HomepageSectionItem,
    FrontPageSettings,
)
from .serializers import (
    SliderRevolutionSerializer,
    SliderRevolutionListSerializer,
    SlideSerializer,
    SlideCreateUpdateSerializer,
    SlideLayerSerializer,
    HomepageSectionSerializer,
    HomepageSectionListSerializer,
    HomepageSectionItemSerializer,
    FrontPageSettingsSerializer,
    FrontPageFullSerializer,
)


class SliderRevolutionViewSet(viewsets.ModelViewSet):
    """ViewSet for Slider Revolution management"""

    queryset = SliderRevolution.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return SliderRevolutionListSerializer
        return SliderRevolutionSerializer

    def get_queryset(self):
        queryset = SliderRevolution.objects.all()

        # Filter by language
        language = self.request.query_params.get('language')
        if language:
            queryset = queryset.filter(language=language)

        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        # Filter by type
        slider_type = self.request.query_params.get('type')
        if slider_type:
            queryset = queryset.filter(slider_type=slider_type)

        return queryset.prefetch_related('slides', 'slides__layers')

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplicate a slider with all its slides and layers"""
        slider = self.get_object()

        # Create new slider
        new_slider = SliderRevolution.objects.create(
            name=f"{slider.name} (Copy)",
            description=slider.description,
            slider_type=slider.slider_type,
            is_active=False,
            width=slider.width,
            height=slider.height,
            autoplay=slider.autoplay,
            autoplay_delay=slider.autoplay_delay,
            loop=slider.loop,
            pause_on_hover=slider.pause_on_hover,
            show_navigation=slider.show_navigation,
            show_bullets=slider.show_bullets,
            show_progress=slider.show_progress,
            language=slider.language,
            custom_css=slider.custom_css,
            custom_js=slider.custom_js,
        )

        # Duplicate slides
        for slide in slider.slides.all():
            new_slide = Slide.objects.create(
                slider=new_slider,
                title=slide.title,
                subtitle=slide.subtitle,
                order=slide.order,
                status='draft',
                background_image=slide.background_image,
                background_color=slide.background_color,
                background_video_url=slide.background_video_url,
                overlay_color=slide.overlay_color,
                content_html=slide.content_html,
                cta_text=slide.cta_text,
                cta_link=slide.cta_link,
                cta_style=slide.cta_style,
                secondary_cta_text=slide.secondary_cta_text,
                secondary_cta_link=slide.secondary_cta_link,
                duration=slide.duration,
                transition=slide.transition,
                transition_duration=slide.transition_duration,
            )

            # Duplicate layers
            for layer in slide.layers.all():
                SlideLayer.objects.create(
                    slide=new_slide,
                    name=layer.name,
                    layer_type=layer.layer_type,
                    order=layer.order,
                    content=layer.content,
                    media_file=layer.media_file,
                    link_url=layer.link_url,
                    link_target=layer.link_target,
                    position_x=layer.position_x,
                    position_y=layer.position_y,
                    offset_x=layer.offset_x,
                    offset_y=layer.offset_y,
                    width=layer.width,
                    height=layer.height,
                    animation_in=layer.animation_in,
                    animation_out=layer.animation_out,
                    start_time=layer.start_time,
                    end_time=layer.end_time,
                    animation_speed=layer.animation_speed,
                    css_class=layer.css_class,
                    custom_style=layer.custom_style,
                    visible_desktop=layer.visible_desktop,
                    visible_tablet=layer.visible_tablet,
                    visible_mobile=layer.visible_mobile,
                )

        serializer = SliderRevolutionSerializer(new_slider)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def create_translation(self, request, pk=None):
        """Create a translation of this slider for another language"""
        slider = self.get_object()
        target_language = request.data.get('language')

        if not target_language:
            return Response(
                {'error': 'Target language is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if translation already exists
        if SliderRevolution.objects.filter(
            translation_of=slider,
            language=target_language
        ).exists():
            return Response(
                {'error': f'Translation for {target_language} already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create translation
        new_slider = SliderRevolution.objects.create(
            name=f"{slider.name} ({target_language.upper()})",
            description=slider.description,
            slider_type=slider.slider_type,
            is_active=False,
            width=slider.width,
            height=slider.height,
            autoplay=slider.autoplay,
            autoplay_delay=slider.autoplay_delay,
            loop=slider.loop,
            pause_on_hover=slider.pause_on_hover,
            show_navigation=slider.show_navigation,
            show_bullets=slider.show_bullets,
            show_progress=slider.show_progress,
            language=target_language,
            translation_of=slider,
            custom_css=slider.custom_css,
            custom_js=slider.custom_js,
        )

        # Copy slides structure (content needs translation)
        for slide in slider.slides.all():
            new_slide = Slide.objects.create(
                slider=new_slider,
                title=slide.title,  # Needs translation
                subtitle=slide.subtitle,  # Needs translation
                order=slide.order,
                status='draft',
                background_image=slide.background_image,
                background_color=slide.background_color,
                background_video_url=slide.background_video_url,
                overlay_color=slide.overlay_color,
                content_html=slide.content_html,  # Needs translation
                cta_text=slide.cta_text,  # Needs translation
                cta_link=slide.cta_link,
                cta_style=slide.cta_style,
                secondary_cta_text=slide.secondary_cta_text,
                secondary_cta_link=slide.secondary_cta_link,
                duration=slide.duration,
                transition=slide.transition,
                transition_duration=slide.transition_duration,
            )

            for layer in slide.layers.all():
                SlideLayer.objects.create(
                    slide=new_slide,
                    name=layer.name,
                    layer_type=layer.layer_type,
                    order=layer.order,
                    content=layer.content,  # Needs translation if text
                    media_file=layer.media_file,
                    link_url=layer.link_url,
                    link_target=layer.link_target,
                    position_x=layer.position_x,
                    position_y=layer.position_y,
                    offset_x=layer.offset_x,
                    offset_y=layer.offset_y,
                    width=layer.width,
                    height=layer.height,
                    animation_in=layer.animation_in,
                    animation_out=layer.animation_out,
                    start_time=layer.start_time,
                    end_time=layer.end_time,
                    animation_speed=layer.animation_speed,
                    css_class=layer.css_class,
                    custom_style=layer.custom_style,
                    visible_desktop=layer.visible_desktop,
                    visible_tablet=layer.visible_tablet,
                    visible_mobile=layer.visible_mobile,
                )

        serializer = SliderRevolutionSerializer(new_slider)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SlideViewSet(viewsets.ModelViewSet):
    """ViewSet for Slide management"""

    queryset = Slide.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return SlideCreateUpdateSerializer
        return SlideSerializer

    def get_queryset(self):
        queryset = Slide.objects.all()

        # Filter by slider
        slider_id = self.request.query_params.get('slider')
        if slider_id:
            queryset = queryset.filter(slider_id=slider_id)

        # Filter by status
        slide_status = self.request.query_params.get('status')
        if slide_status:
            queryset = queryset.filter(status=slide_status)

        return queryset.select_related('slider', 'background_image').prefetch_related('layers')

    @action(detail=True, methods=['post'])
    def reorder(self, request, pk=None):
        """Update slide order"""
        slide = self.get_object()
        new_order = request.data.get('order')

        if new_order is None:
            return Response(
                {'error': 'Order is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        slide.order = new_order
        slide.save(update_fields=['order'])

        return Response({'status': 'order updated', 'order': new_order})

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Publish a slide"""
        slide = self.get_object()
        slide.status = 'published'
        slide.save(update_fields=['status'])

        return Response({'status': 'published'})

    @action(detail=True, methods=['post'])
    def unpublish(self, request, pk=None):
        """Unpublish a slide"""
        slide = self.get_object()
        slide.status = 'draft'
        slide.save(update_fields=['status'])

        return Response({'status': 'draft'})


class SlideLayerViewSet(viewsets.ModelViewSet):
    """ViewSet for Slide Layer management"""

    queryset = SlideLayer.objects.all()
    serializer_class = SlideLayerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = SlideLayer.objects.all()

        # Filter by slide
        slide_id = self.request.query_params.get('slide')
        if slide_id:
            queryset = queryset.filter(slide_id=slide_id)

        # Filter by type
        layer_type = self.request.query_params.get('type')
        if layer_type:
            queryset = queryset.filter(layer_type=layer_type)

        return queryset.select_related('slide', 'media_file')


class HomepageSectionViewSet(viewsets.ModelViewSet):
    """ViewSet for Homepage Section management"""

    queryset = HomepageSection.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return HomepageSectionListSerializer
        return HomepageSectionSerializer

    def get_queryset(self):
        queryset = HomepageSection.objects.all()

        # Filter by language
        language = self.request.query_params.get('language')
        if language:
            queryset = queryset.filter(language=language)

        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        # Filter by section type
        section_type = self.request.query_params.get('type')
        if section_type:
            queryset = queryset.filter(section_type=section_type)

        return queryset.prefetch_related('items', 'slider')

    @action(detail=False, methods=['get'])
    def ordered(self, request):
        """Get sections in display order for a language"""
        language = request.query_params.get('language', 'de')
        sections = HomepageSection.objects.filter(
            language=language,
            is_active=True
        ).order_by('order').prefetch_related('items', 'slider')

        serializer = HomepageSectionSerializer(sections, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def reorder(self, request, pk=None):
        """Update section order"""
        section = self.get_object()
        new_order = request.data.get('order')

        if new_order is None:
            return Response(
                {'error': 'Order is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        section.order = new_order
        section.save(update_fields=['order'])

        return Response({'status': 'order updated', 'order': new_order})

    @action(detail=False, methods=['post'])
    def bulk_reorder(self, request):
        """Bulk update section orders"""
        orders = request.data.get('orders', [])

        for item in orders:
            section_id = item.get('id')
            order = item.get('order')
            if section_id and order is not None:
                HomepageSection.objects.filter(id=section_id).update(order=order)

        return Response({'status': 'orders updated'})


class HomepageSectionItemViewSet(viewsets.ModelViewSet):
    """ViewSet for Homepage Section Item management"""

    queryset = HomepageSectionItem.objects.all()
    serializer_class = HomepageSectionItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = HomepageSectionItem.objects.all()

        # Filter by section
        section_id = self.request.query_params.get('section')
        if section_id:
            queryset = queryset.filter(section_id=section_id)

        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        return queryset.select_related('section', 'image')

    @action(detail=False, methods=['post'])
    def bulk_reorder(self, request):
        """Bulk update item orders within a section"""
        orders = request.data.get('orders', [])

        for item in orders:
            item_id = item.get('id')
            order = item.get('order')
            if item_id and order is not None:
                HomepageSectionItem.objects.filter(id=item_id).update(order=order)

        return Response({'status': 'orders updated'})


class FrontPageSettingsViewSet(viewsets.ModelViewSet):
    """ViewSet for Front Page Settings management"""

    queryset = FrontPageSettings.objects.all()
    serializer_class = FrontPageSettingsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = FrontPageSettings.objects.all()

        # Filter by language
        language = self.request.query_params.get('language')
        if language:
            queryset = queryset.filter(language=language)

        return queryset

    @action(detail=False, methods=['get'])
    def by_language(self, request):
        """Get settings for a specific language, creating if not exists"""
        language = request.query_params.get('language', 'de')

        settings, created = FrontPageSettings.objects.get_or_create(
            language=language,
            defaults={'meta_title': f'Pro-FM Facility Management'}
        )

        serializer = FrontPageSettingsSerializer(settings)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def full_page(self, request):
        """Get complete front page data for rendering"""
        language = request.query_params.get('language', 'de')

        # Get or create settings
        settings, _ = FrontPageSettings.objects.get_or_create(
            language=language,
            defaults={'meta_title': f'Pro-FM Facility Management'}
        )

        # Get main slider
        main_slider = settings.main_slider
        if main_slider:
            main_slider = SliderRevolution.objects.prefetch_related(
                'slides', 'slides__layers'
            ).get(id=main_slider.id)

        # Get active sections
        sections = HomepageSection.objects.filter(
            language=language,
            is_active=True
        ).order_by('order').prefetch_related('items', 'slider')

        # Build response
        data = {
            'settings': FrontPageSettingsSerializer(settings).data,
            'main_slider': SliderRevolutionSerializer(main_slider).data if main_slider else None,
            'sections': HomepageSectionSerializer(sections, many=True).data,
        }

        return Response(data)
