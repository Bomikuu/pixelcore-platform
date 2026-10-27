from celery import shared_task


@shared_task(name="businesses.smokey.generate", autoretry_for=())
def generate_smokey_report(request_id):
    from smokey_assistant.generation import run_generation
    from .smokey_bridge import worker_context
    from .smokey_reports import resolve_report

    run_generation(request_id, worker_context, resolve_report)


@shared_task(name="businesses.smokey.recover")
def recover_smokey_reports():
    from smokey_assistant.generation import recover_expired

    return recover_expired()
