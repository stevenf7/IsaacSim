// Copyright (c) 2022-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once
#include <carb/extras/Library.h>
#include <carb/logging/Log.h>

#include <vector>
namespace omni
{
namespace isaac
{
namespace utils
{


class LibraryLoader
{
public:
    std::string loadedLibraryFile;
    carb::extras::LibraryHandle loadedLibrary = carb::extras::kInvalidLibraryHandle;

    LibraryLoader(std::string library, std::string prefix = "", bool test = false)
    {
        {
#ifdef _MSC_VER
            std::string libraryPath = prefix + library + ".dll";
#else
            std::string libraryPath = prefix + "lib" + library + ".so";
#endif
            loadedLibraryFile = libraryPath;
            // printf("Loading %s\n", libraryPath.c_str());
            // loadedLibrary = dlopen(libraryPath.c_str(), RTLD_NOW | RTLD_GLOBAL);
            loadedLibrary = carb::extras::loadLibrary(libraryPath.c_str(), carb::extras::fLibFlagNow);

            if (loadedLibrary == carb::extras::kInvalidLibraryHandle)
            {
                if (test)
                {
                    printf("Could not load the dynamic library from %s. Error: %s\n", libraryPath.c_str(),
                           carb::extras::getLastLoadLibraryError().c_str());
                }
                else
                {
                    printf("Could not load the dynamic library from %s. Error: %s\n", libraryPath.c_str(),
                           carb::extras::getLastLoadLibraryError().c_str());
                }

                loadedLibrary = carb::extras::kInvalidLibraryHandle;
            }
        }
    }

    ~LibraryLoader()
    {
        if (loadedLibrary)
        {
            // printf("Destructor for %s \n", loadedLibraryFile.c_str());
            // dlclose(loadedLibrary);
            carb::extras::unloadLibrary(loadedLibrary);
        }
        loadedLibrary = carb::extras::kInvalidLibraryHandle;
    }

    template <typename T>
    T getSymbol(std::string symbol)
    {
        return carb::extras::getLibrarySymbol<T>(loadedLibrary, symbol.c_str());
    }

    template <typename T>
    T callSymbol(std::string symbol)
    {
        typedef T binding();
        void* loadedSymbol = getSymbol<void*>(symbol.c_str());

        if (!loadedSymbol)
        {
            printf("%s does not contain %s\n", loadedLibraryFile.c_str(), symbol.c_str());
            return nullptr;
        }
        binding* calledSymbol = reinterpret_cast<binding*>(loadedSymbol);

        return calledSymbol();
    }

    template <typename T, typename... Arguments>
    T callSymbolWithArg(std::string symbol, Arguments... args)
    {
        typedef T binding(Arguments...);
        void* loadedSymbol = getSymbol<void*>(symbol.c_str());

        if (!loadedSymbol)
        {
            printf("%s does not contain %s\n", loadedLibraryFile.c_str(), symbol.c_str());
        }

        binding* calledSymbol = reinterpret_cast<binding*>(loadedSymbol);

        return calledSymbol(args...);
    }


private:
};

class MultiLibraryLoader
{
public:
    ~MultiLibraryLoader()
    {
        loadedLibraries.clear();
    }

    std::shared_ptr<LibraryLoader> LoadLibrary(const std::string library, std::string prefix = "")
    {
        auto loadedLib = std::make_shared<LibraryLoader>(library, prefix);
        loadedLibraries.emplace_back(loadedLib);
        return loadedLib;
    }

private:
    std::vector<std::shared_ptr<LibraryLoader>> loadedLibraries;
};


}
}
}
