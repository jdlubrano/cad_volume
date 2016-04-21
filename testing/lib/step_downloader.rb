require 'aws-sdk'

require_relative 'local_asset'
require_relative 'part'

class StepDownloader
  BUCKET_NAME = 'maketime-server-app'
  def initialize
    credentials = Aws::SharedCredentials.new(profile_name: 'maketime')
    @client = Aws::S3::Client.new(credentials: credentials, region: 'us-west-2')
    @resource = Aws::S3::Resource.new(client: @client)
    @bucket = @resource.bucket(BUCKET_NAME)
  end

  def list
    if @bucket.exists?
      @bucket.objects.limit(3).each do |obj|
        puts "#{obj.key} => #{obj.etag}"
      end
    else
      puts 'Bucket does not exist'
    end
  end

  def get_object(part)
    key = "uploads/parts/#{part['part_id']}/#{part['file']}"
    begin
      @client.get_object(
        response_target: LocalAsset.path(part),
        bucket: BUCKET_NAME,
        key: key
      )
    rescue Aws::S3::Errors::NoSuchKey => e
      puts "#{e}: #{key}"
    end
  end

  def get_step_files
    Part.all do |part|
      next if File.exist? LocalAsset.path(part)
      get_object(part)
    end
  end
end

