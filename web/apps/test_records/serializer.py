from rest_framework import serializers

from pgperffarm.settings import DB_ENUM
from test_records.models import TestRecord, TestResult, PGInfo, LinuxInfo, MetaInfo, TestDataSet, TestCategory
from users.serializer import UserMachineSerializer
from users.models import UserMachine
from django.db.models import Count


class TestCategorySerializer(serializers.ModelSerializer):
    '''
    use TestCategorySerializer
    '''

    class Meta:
        model = TestCategory
        fields = ('cate_name', 'cate_sn')


class PGInfoSerializer(serializers.ModelSerializer):
    '''
    use PGInfoSerializer
    '''

    class Meta:
        model = PGInfo
        fields = ('pg_branch',)


class LinuxInfoSerializer(serializers.ModelSerializer):
    '''
    use LinuxInfoSerializer
    '''

    class Meta:
        model = LinuxInfo
        fields = ('mounts', 'cpuinfo', 'sysctl', 'meminfo')


class MetaInfoSerializer(serializers.ModelSerializer):
    '''
    use MetaInfoSerializer
    '''

    class Meta:
        model = MetaInfo
        fields = ('date', 'uname', 'benchmark', 'name')


class TestResultSerializer(serializers.ModelSerializer):
    '''
    use TestResultSerializer
    '''

    class Meta:
        model = TestResult
        fields = "__all__"


class CreateTestRecordSerializer(serializers.ModelSerializer):
    '''
    create ModelSerializer
    '''

    # pg_info =PGInfoSerializer()
    # linux_info = LinuxInfoSerializer()
    # meta_info = MetaInfoSerializer()

    class Meta:
        model = TestRecord
        fields = "__all__"


class CreateTestDateSetSerializer(serializers.ModelSerializer):
    '''
    create TestDateSetSerializer
        'test_record': testRecordRet.id,
        'clients': client_num,
        'scale': scale,
        'std': dataset['std'],
        'metric': dataset['metric'],
        'median': dataset['median'],
        'test_cate': test_cate.id,
        # status,percentage calc by tarr
        'status': -1,
        'percentage': 0.0,
    '''

    class Meta:
        model = TestDataSet
        fields = "__all__"


class TestRecordListSerializer(serializers.ModelSerializer):
    '''
    use ModelSerializer
    '''
    pg_info = PGInfoSerializer()
    linux_info = LinuxInfoSerializer()
    meta_info = MetaInfoSerializer()

    trend = serializers.SerializerMethodField()
    machine_info = serializers.SerializerMethodField()

    # client_max_num = serializers.SerializerMethodField()
    class Meta:
        model = TestRecord
        fields = ('uuid', 'add_time', 'machine_info', 'pg_info', 'trend', 'linux_info', 'meta_info')

    def get_trend(self, obj):
        dataset_list = TestDataSet.objects.filter(test_record_id=obj.id).values_list('status').annotate(Count('id'))
        data_list_count = TestDataSet.objects.filter(test_record_id=obj.id).count()

        trend = {}
        trend['improved'] = 0
        trend['quo'] = 0
        trend['regressive'] = 0
        trend['none'] = 0
        trend['is_first'] = False
        for i in dataset_list:
            if i[0] == DB_ENUM['status']['improved']:
                trend['improved'] += i[1]
            elif i[0] == DB_ENUM['status']['quo']:
                trend['quo'] += i[1]
            elif i[0] == DB_ENUM['status']['regressive']:
                trend['regressive'] += i[1]
            elif i[0] == DB_ENUM['status']['none']:
                trend['none'] += i[1]

        if (data_list_count == trend['none']):
            trend['is_first'] = True

        print str(data_list_count)
        return trend

    def get_machine_info(self, obj):
        machine_data = UserMachine.objects.filter(id=obj.test_machine_id)

        machine_info_serializer = UserMachineSerializer(machine_data, many=True,
                                                        context={'request': self.context['request']})
        return machine_info_serializer.data

    # def get_client_max_num(self, obj):
    #     ro_client_num = TestResult.objects.filter(Q(test_record_id=obj.id ) ,test_cate_id=1).order_by('clients').distinct('clients').count()
    #     rw_client_num = TestResult.objects.filter(Q(test_record_id=obj.id ) ,test_cate_id=2).order_by('clients').distinct('clients').count()
    #     return max(ro_client_num,rw_client_num)


class TestDataSetDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestDataSet
        fields = "__all__"


class TestRecordDetailSerializer(serializers.ModelSerializer):
    '''
    use ModelSerializer
    '''
    pg_info = PGInfoSerializer()
    linux_info = LinuxInfoSerializer()
    test_machine = UserMachineSerializer()
    meta_info = MetaInfoSerializer()
    dataset_info = serializers.SerializerMethodField()

    # rw_info = serializers.SerializerMethodField()
    class Meta:
        model = TestRecord
        fields = (
            'uuid', 'pg_info', 'linux_info', 'meta_info', 'dataset_info', 'test_desc', 'meta_time', 'test_machine')

    def get_dataset_info(self, obj):
        dataset_list = TestDataSet.objects.filter(test_record_id=obj.id).values_list('test_cate_id').annotate(
            Count('id'))
        # print(target_dataset)

        dataset = {}
        # < QuerySet[(1, 3), (2, 3)] >

        for cate_item in dataset_list:

            cate_info = TestCategory.objects.filter(id=cate_item[0]).first()
            cate_info_serializer = TestCategorySerializer(cate_info)
            cate_sn = cate_info_serializer.data["cate_sn"]
            dataset[cate_sn] = {}

            dataset_scale_list = TestDataSet.objects.filter(test_record_id=obj.id, test_cate=cate_item[0]).values_list(
                'scale').annotate(Count('id'))
            # print(dataset_scale_list) <QuerySet [(10, 2), (20, 1)]>
            for scale_item in dataset_scale_list:
                dataset[cate_sn][scale_item[0]] = {}

                dataset_client_list = TestDataSet.objects.filter(test_record_id=obj.id,test_cate=cate_item[0]).values_list('clients').annotate( Count('id'))
                # print(dataset_client_list) <QuerySet [(1, 1), (2, 1), (4, 1)]>
                for client_item in dataset_client_list:
                    dataset[cate_sn][scale_item[0]][client_item[0]] = []

                # target_dataset = TestDataSet.objects.filter(test_record_id=obj.id, test_cate=cate_item[0],
                #                                             scale=scale_item[0])
                # dataset_serializer = TestDataSetDetailSerializer(target_dataset, many=True)
                # dataset[cate_sn][scale_item[0]] = dataset_serializer.data

        return dataset

    # def get_ro_info(self, obj):
    #     all_data = TestResult.objects.filter(Q(test_record_id=obj.id ) ,test_cate_id=1)
    #
    #     ro_info_serializer = TestResultSerializer(all_data, many=True, context={'request': self.context['request']})
    #     return ro_info_serializer.data
    #
    # def get_rw_info(self, obj):
    #     all_data = TestResult.objects.filter(Q(test_record_id=obj.id) ,test_cate_id=2)
    #
    #     rw_info_serializer = TestResultSerializer(all_data, many=True, context={'request': self.context['request']})
    #     return rw_info_serializer.data
