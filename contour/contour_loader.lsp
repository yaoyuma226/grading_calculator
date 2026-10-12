; Optional AutoCAD loader: defines command MAKECONTOURS.
; 1. Edit PYTHON_SCRIPT below to the full path of make_contours.py
;    on her machine (use double backslashes).
; 2. APPLOAD this file (or add to Startup Suite).
; 3. In AutoCAD: select elevation texts, then type MAKECONTOURS.
; The command prompts for the contour interval.

(defun c:MAKECONTOURS ( / script interval cmd)
  (setq script "C:\\grading_calculator\\contour\\make_contours.py")
  (setq interval (getreal "\nContour interval (same unit as elevations) <1.0>: "))
  (if (null interval) (setq interval 1.0))
  ;; pick-first selection is used, so nothing to pass; just launch python
  (setq cmd (strcat "pythonw \"" script "\" --interval " (rtos interval 2 4)))
  (startapp "cmd" (strcat "/c start \"\" " cmd))
  (princ "\nGenerating contours... check AutoCAD in a moment.")
  (princ)
)
