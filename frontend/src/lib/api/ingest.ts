import { apiRequest } from './client';

export type FileFormat = 'jsonl' | 'csv' | 'txt' | 'pdf' | 'docx' | 'png' | 'jpg' | 'jpeg';

export interface PresignedUploadRequest {
	file_name: string;
	file_format: FileFormat;
	file_size_bytes: number;
	class_id: string;
	date: string; // ISO date string
	content_type?: string;
}

export interface PresignedUploadResponse {
	upload_url: string;
	artifact_id: string;
	s3_key: string;
	expires_at: string;
	upload_method: string;
}

export interface TranscriptMetadata {
	class_id: string;
	date: string; // ISO date string
	student_roster: string[];
	source: string;
}

export interface TranscriptIngestRequest {
	artifact_id: string;
	metadata: TranscriptMetadata;
}

export interface TranscriptIngestResponse {
	job_id: string;
	artifact_id: string;
	status: string;
	message: string;
	class_id: string;
	date: string;
}

export interface ArtifactMetadata {
	class_id: string;
	date: string; // ISO date string
	student_id: string;
	artifact_type: string;
}

export interface ArtifactIngestRequest {
	artifact_id: string;
	metadata: ArtifactMetadata;
}

export interface ArtifactIngestResponse {
	job_id: string;
	artifact_id: string;
	status: string;
	message: string;
	class_id: string;
	student_id: string;
	date: string;
}

export async function requestPresignedUpload(
	request: PresignedUploadRequest
): Promise<PresignedUploadResponse> {
	return apiRequest<PresignedUploadResponse>('POST:/v1/ingest/presigned-upload', {
		body: request
	});
}

export async function uploadToS3(url: string, file: File, contentType: string): Promise<void> {
	const response = await fetch(url, {
		method: 'PUT',
		body: file,
		headers: {
			'Content-Type': contentType
		}
	});

	if (!response.ok) {
		throw new Error(`S3 upload failed: ${response.statusText}`);
	}
}

export async function ingestTranscript(
	request: TranscriptIngestRequest
): Promise<TranscriptIngestResponse> {
	return apiRequest<TranscriptIngestResponse>('POST:/v1/ingest/transcripts', {
		body: request
	});
}

export async function ingestArtifact(
	request: ArtifactIngestRequest
): Promise<ArtifactIngestResponse> {
	return apiRequest<ArtifactIngestResponse>('POST:/v1/ingest/artifacts', {
		body: request
	});
}
