require 'awesome_print'
require 'aws-sdk'
require 'pg'
require 'byebug'

class DbCxn
  def initialize
    @cxn = PG.connect(dbname: 'test_parts')
  end

  def exec(sql)
    @cxn.exec(sql) { |result| yield result }
  end
end

class Bucket
  def initialize
    credentials = Aws::SharedCredentials.new(profile_name: 'maketime')
    @client = Aws::S3::Client.new(credentials: credentials, region: 'us-west-2')
    @resource = Aws::S3::Resource.new(client: @client)
    @bucket = @resource.bucket('maketime-server-app')
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
end

db = DbCxn.new

db.exec('SELECT * FROM parts LIMIT 1') do |result|
  byebug
end

bucket = Bucket.new
bucket.list

