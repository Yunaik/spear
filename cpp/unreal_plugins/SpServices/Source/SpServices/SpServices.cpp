//
// Copyright(c) 2022 Intel. Licensed under the MIT License <http://opensource.org/licenses/MIT>.
//

#include "SpServices/SpServices.h"

#include <memory> // std::make_unique, std::unique_ptr

#include <Modules/ModuleManager.h> // IMPLEMENT_MODULE

#include "SpCore/Assert.h"
#include "SpCore/AssertModuleLoaded.h"
#include "SpCore/Config.h"
#include "SpCore/Log.h"
#include "SpCore/Rpclib.h"
#include "SpCore/Unreal.h"

#include "SpServices/CppFuncService.h"
#include "SpServices/EngineService.h"
#include "SpServices/LegacyService.h"
#include "SpServices/UnrealService.h"

void SpServices::StartupModule()
{
    SP_ASSERT_MODULE_LOADED("SpCore");
    SP_ASSERT_MODULE_LOADED("UrdfRobot");
    SP_ASSERT_MODULE_LOADED("Vehicle");
    SP_LOG_CURRENT_FUNCTION();

    if (Config::isInitialized()) {
        rpc_server_ = std::make_unique<rpc::server>(Config::get<int>("SP_SERVICES.PORT"));
    } else {
        rpc_server_ = std::make_unique<rpc::server>(30000);
    }
    SP_ASSERT(rpc_server_);

    // EngineService needs its own custom logic for binding its entry points, because they are
    // intended to run directly on the RPC server worker thread, whereas all other entry points
    // are intended to run on work queues maintained by EngineService. So we pass in the server
    // when constructing EngineService, and we pass in EngineService when constructing all other
    // services.
    engine_service_ = std::make_unique<EngineService<rpc::server>>(rpc_server_.get());

    cpp_func_service_ = std::make_unique<CppFuncService>(engine_service_.get());
    legacy_service_ = std::make_unique<LegacyService>(engine_service_.get());
    unreal_service_ = std::make_unique<UnrealService>(engine_service_.get());

    int num_worker_threads = 1;
    rpc_server_->async_run(num_worker_threads);
}

void SpServices::ShutdownModule()
{
    SP_LOG_CURRENT_FUNCTION();

    SP_ASSERT(engine_service_);
    engine_service_->close();

    SP_ASSERT(rpc_server_);
    rpc_server_->close_sessions();
    rpc_server_->stop();

    SP_ASSERT(unreal_service_);
    SP_ASSERT(legacy_service_);
    SP_ASSERT(cpp_func_service_);
    unreal_service_ = nullptr;
    legacy_service_ = nullptr;
    cpp_func_service_ = nullptr;

    SP_ASSERT(engine_service_);
    engine_service_ = nullptr;

    rpc_server_ = nullptr;
}

IMPLEMENT_MODULE(SpServices, SpServices)
