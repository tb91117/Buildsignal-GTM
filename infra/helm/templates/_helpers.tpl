{{- define "buildsignal.name" -}}
buildsignal
{{- end -}}

{{- define "buildsignal.labels" -}}
app.kubernetes.io/name: {{ include "buildsignal.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{- define "buildsignal.selectorLabels" -}}
app.kubernetes.io/name: {{ include "buildsignal.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
