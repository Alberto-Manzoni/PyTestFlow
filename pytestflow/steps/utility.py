from pytestflow.core import StepWrapper
from pytestflow.core.pytestflow_states import PyTestflowDone
from pytestflow.steps.common import get_metadata_from_prefect_context
from PyQt5.QtWidgets import QApplication, QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import QTimer
import sys


class MsgBoxDialog(QDialog):
    def __init__(self, message="Message", input_enabled=False, timeout=None):
        super().__init__()
        self.setWindowTitle("PyTestFlow")
        self.value = None
        self.user_pressed = None

        layout = QVBoxLayout()
        layout.addWidget(QLabel(message))

        self.input_enabled = input_enabled
        self.input_field = QLineEdit()
        if input_enabled:
            layout.addWidget(self.input_field)

        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        self.ok_button.clicked.connect(self.ok_clicked)
        self.cancel_button.clicked.connect(self.cancel_clicked)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        if timeout:
            QTimer.singleShot(timeout * 1000, self.auto_close)

    def ok_clicked(self):
        self.user_pressed = "ok"
        self.value = self.input_field.text() if self.input_enabled else None
        self.accept()

    def cancel_clicked(self):
        self.user_pressed = "cancel"
        self.value = None
        self.reject()

    def auto_close(self):
        if self.user_pressed is None:
            print("[INFO] Auto-closing dialog (timeout reached)")
            self.user_pressed = "timeout"
            self.value = None
            self.reject()


class MsgBoxStep(StepWrapper):
    def __init__(
        self,
        fn,
        *,
        message="Message",
        input_enabled=False,
        timeout=None,
        store_as=None,
        default=None,
        name=None,
        autowire=True,
        **task_kwargs
    ):
        # don't pass default downstream
        task_kwargs.pop("default", None)
        super().__init__(fn, name=name, autowire=autowire, **task_kwargs)
        self.message = message
        self.input_enabled = input_enabled
        self.timeout = timeout
        self.store_as = store_as
        self.default = default

    def _run(self, *args, **kwargs):
        from pytestflow.core.context import ptf_context

        app = QApplication.instance()
        created_app = False
        if not app:
            app = QApplication(sys.argv)
            created_app = True

        dialog = MsgBoxDialog(message=self.message, input_enabled=self.input_enabled, timeout=self.timeout)

        if created_app:
            dialog.show()
            app.exec_()
            # optional cleanup (helps in some test runners)
            try:
                app.quit()
            except Exception:
                pass
        else:
            dialog.exec_()

        if dialog.user_pressed == "ok":
            value = dialog.value
        elif dialog.user_pressed == "timeout":
            value = self.default
        else:
            value = None

        if self.store_as:
            ptf_context.locals[self.store_as] = value

        result_data = {
            "step_status": "done",
            "output": value,
            "message": self.message,
            "button_pressed": dialog.user_pressed,
            "store_as": self.store_as,
            "default": self.default,
            "step_type": "msgbox_qt",
        }

        result_data.update(self.get_meta_info())
        result_data.update(get_metadata_from_prefect_context())

        return PyTestflowDone(ptf_result=result_data)


def msgbox_step_qt(*, message="Message", input_enabled=False, timeout=None,
                   store_as=None, default=None, name=None, autowire=True, **task_kwargs):
    """
    Decorator factory for message box steps.
    """
    def decorator(fn):
        # IMPORTANT: already task-wrapped by StepWrapper
        return MsgBoxStep(
            fn,
            message=message,
            input_enabled=input_enabled,
            timeout=timeout,
            store_as=store_as,
            default=default,
            name=name,
            autowire=autowire,
            **task_kwargs,
        )
    return decorator
