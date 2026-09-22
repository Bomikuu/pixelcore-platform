import re
import uuid

from rest_framework import serializers


def validate_hero_slides(slides, business=None):
    from businesses.models import BusinessAsset

    if not isinstance(slides, list) or len(slides) > 5:
        raise serializers.ValidationError('Use up to five custom hero slides.')
    allowed = {'id', 'type', 'heading', 'body', 'asset_id', 'poster_asset_id', 'label', 'path', 'background_color', 'motion'}
    result, seen = [], set()
    for source in slides:
        if not isinstance(source, dict) or set(source) - allowed:
            raise serializers.ValidationError('A hero slide contains unsupported settings.')
        slide = {**source}
        for field, maximum in [('id', 80), ('heading', 180), ('body', 600), ('label', 80), ('path', 300)]:
            value = slide.get(field, '')
            if not isinstance(value, str) or len(value) > maximum:
                raise serializers.ValidationError(f'Invalid hero slide {field}.')
            slide[field] = value.strip()
        if not slide['id'] or slide['id'] in seen:
            raise serializers.ValidationError('Every hero slide needs a unique ID.')
        seen.add(slide['id'])
        if not isinstance(slide.get('type'), str) or slide['type'] not in {'image', 'video', 'model', 'particles'}:
            raise serializers.ValidationError('Choose image, video, model, or particles.')
        if slide['path'] and not re.fullmatch(r'/[A-Za-z0-9/_-]*', slide['path']):
            raise serializers.ValidationError('Hero links must be internal storefront paths.')
        slide['background_color'] = slide.get('background_color', '#17362F')
        if not isinstance(slide['background_color'], str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', slide['background_color']):
            raise serializers.ValidationError('Use a six-digit hero background color.')
        slide['motion'] = slide.get('motion', 'subtle')
        if not isinstance(slide['motion'], str) or slide['motion'] not in {'none', 'subtle', 'interactive'}:
            raise serializers.ValidationError('Choose an approved motion setting.')
        for field in ['asset_id', 'poster_asset_id']:
            value = slide.get(field, '')
            try:
                slide[field] = str(uuid.UUID(str(value))) if value else ''
            except (ValueError, TypeError, AttributeError):
                raise serializers.ValidationError('Choose media from the business library.')
            if value and business:
                expected = 'image' if field == 'poster_asset_id' else {'model': 'model', 'video': 'video'}.get(slide['type'], 'image')
                if not BusinessAsset.objects.filter(business=business, public_id=slide[field], asset_type=expected, processing_status='ready').exists():
                    raise serializers.ValidationError('Hero media must be approved assets owned by this business.')
        if slide['type'] != 'particles' and not slide['asset_id']:
            raise serializers.ValidationError('Choose the background media for each slide.')
        if slide['type'] in {'video', 'model'} and not slide['poster_asset_id']:
            raise serializers.ValidationError('Video and 3D slides need a poster image fallback.')
        result.append(slide)
    return result


def hero_asset_ids(slides):
    return {slide[key] for slide in slides for key in ('asset_id', 'poster_asset_id') if slide.get(key)}


def public_hero_assets(business, slides):
    from businesses.models import BusinessAsset
    return [{'public_id': str(asset.public_id), 'url': asset.file.url, 'asset_type': asset.asset_type, 'alt_text': asset.alt_text}
            for asset in BusinessAsset.objects.filter(business=business, public_id__in=hero_asset_ids(slides), processing_status='ready')]
